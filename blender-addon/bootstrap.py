"""Blender lifecycle bootstrap for the stream session manager.

Injected at launch with:
    Blender --python bootstrap.py -- --bsm-port <port>

Blender starts completely normally (splash screen, recent files, full UI);
this script only adds a small lifecycle client that:

  1. connects to the session manager over a localhost TCP socket (JSON lines,
     stdlib only -- nothing is installed into Blender's bundled Python),
  2. on {"type": "shutdown_request"}: saves the project, replies with
     {"type": "shutdown_ack", "status": "saved"}, and quits Blender cleanly,
  3. if the socket drops (session manager crashed): saves and quits anyway,
     so no orphaned Blender processes are left behind.

Save behavior (Cmd+S equivalent):
  - file has a path     -> overwrite save (bpy.ops.wm.save_mainfile)
  - file never saved    -> save to ~/Library/Application Support/blender_stream/
                           (not /tmp: it must survive reboots for session restore)

All bpy access happens on Blender's main thread via bpy.app.timers; the
socket runs on a background thread and communicates through a queue.
"""

import json
import os
import queue
import socket
import sys
import threading
import time
from datetime import datetime

import bpy

AUTOSAVE_DIR = os.path.expanduser("~/Library/Application Support/blender_stream")

_inbox: "queue.Queue[dict]" = queue.Queue()
_sock_lock = threading.Lock()
_sock = None
_shutting_down = False


def _parse_port() -> int:
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        for i, a in enumerate(args):
            if a == "--bsm-port" and i + 1 < len(args):
                return int(args[i + 1])
    raise SystemExit("bootstrap.py: missing --bsm-port argument")


def _send(msg: dict):
    global _sock
    with _sock_lock:
        if _sock is None:
            return
        try:
            _sock.sendall((json.dumps(msg) + "\n").encode())
        except OSError:
            pass


def _reader_thread(port: int):
    global _sock
    sock = None
    for _ in range(40):  # ~10s of connection attempts
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=5)
            break
        except OSError:
            time.sleep(0.25)
    if sock is None:
        print("[blender-stream] could not reach session manager, lifecycle disabled")
        return

    with _sock_lock:
        _sock = sock
    _send({
        "type": "hello",
        "pid": os.getpid(),
        "blender_version": bpy.app.version_string,
    })

    buf = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    _inbox.put(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass

    # Socket gone: the session manager died or closed us out. Treat as an
    # implicit shutdown request so Blender never lingers as an orphan.
    if not _shutting_down:
        _inbox.put({"type": "shutdown_request", "reason": "manager_lost"})


def _save_project() -> dict:
    """Cmd+S equivalent. Returns {"status": ..., "path": ...}."""
    try:
        if bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
            return {"status": "saved", "path": bpy.data.filepath}
        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(AUTOSAVE_DIR, f"session_autosave_{stamp}.blend")
        # copy=False: the session file becomes the open file, so it shows up
        # in Recent Files when Blender is next launched.
        bpy.ops.wm.save_as_mainfile(filepath=path, copy=False)
        return {"status": "saved", "path": path}
    except Exception as exc:  # save must never block shutdown
        print(f"[blender-stream] save failed: {exc}")
        return {"status": "save_failed", "path": None}


def _force_exit():
    # Last-resort exit if the operator path hangs; data was already saved.
    os._exit(0)


def _do_shutdown(reason: str):
    global _shutting_down
    if _shutting_down:
        return
    _shutting_down = True
    print(f"[blender-stream] shutdown requested ({reason}); saving...")

    result = _save_project()
    _send({"type": "shutdown_ack", "status": result["status"], "path": result["path"]})

    # Give the ack a moment to flush, then quit.
    time.sleep(0.2)
    try:
        bpy.ops.wm.quit_blender()
    except Exception as exc:
        print(f"[blender-stream] quit_blender failed ({exc}), forcing exit")
        _force_exit()
    # If the quit operator returned without actually quitting, force-exit
    # shortly after (the manager would SIGKILL us otherwise).
    threading.Timer(3.0, _force_exit).start()


def _pump_inbox():
    """Runs on Blender's main thread via bpy.app.timers."""
    while True:
        try:
            msg = _inbox.get_nowait()
        except queue.Empty:
            break
        kind = msg.get("type")
        if kind == "shutdown_request":
            _do_shutdown(msg.get("reason", "unknown"))
            return None  # stop the timer; we're exiting
        if kind == "ping":
            _send({"type": "pong"})
    return 0.2


def main():
    port = _parse_port()
    threading.Thread(target=_reader_thread, args=(port,), daemon=True, name="bsm-lifecycle").start()
    bpy.app.timers.register(_pump_inbox, first_interval=0.5, persistent=True)
    print(f"[blender-stream] lifecycle client started (manager port {port})")


main()
