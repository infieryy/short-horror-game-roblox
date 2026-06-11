"""Single-Blender-session orchestrator.

State machine:

    IDLE -> LAUNCHING -> RUNNING <-> DRAINING (client gone, grace running)
                            |             |
                            +--> SHUTTING_DOWN --> IDLE

- Browser connect on IDLE launches Blender (normal launch: splash screen,
  recent files -- the bootstrap script only adds a lifecycle socket).
- Browser disconnect starts a grace timer (page refresh survives).
- Grace expiry or heartbeat timeout triggers the graceful shutdown flow:
  shutdown_request -> wait shutdown_ack(saved) -> wait exit -> SIGTERM -> SIGKILL.
- Blender quitting on its own (File > Quit) returns the session to IDLE and
  notifies the browser, which offers a relaunch button.
"""

import asyncio
import json
import logging
import os
import signal
import struct
import sys
import time
from enum import Enum
from typing import Optional

from blender_channel import BlenderChannel
from capture import CaptureProcess
from config import settings
from input_injector import InputInjector
from window_tracker import WindowTracker, wait_for_blender_window

log = logging.getLogger(__name__)

FRAME_HEADER = struct.Struct(">BQ")  # flags, pts_us

INPUT_TYPES = {"mouse_move", "mouse_down", "mouse_up", "wheel", "key_down", "key_up"}


class SessionState(str, Enum):
    IDLE = "idle"
    LAUNCHING = "launching"
    RUNNING = "running"
    DRAINING = "draining"
    SHUTTING_DOWN = "shutting_down"


class StreamSession:
    def __init__(self):
        self.state = SessionState.IDLE
        self.client = None  # starlette WebSocket
        self.last_seen_ping = time.monotonic()

        self.blender_proc: Optional[asyncio.subprocess.Process] = None
        self.channel: Optional[BlenderChannel] = None
        self.capture: Optional[CaptureProcess] = None
        self.tracker: Optional[WindowTracker] = None
        self.injector: Optional[InputInjector] = None

        self._capture_failures = 0
        self._capture_started_at = 0.0
        self._lock = asyncio.Lock()
        self._grace_task: Optional[asyncio.Task] = None
        self._resize_task: Optional[asyncio.Task] = None
        self._exit_watch_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------- lifecycle

    async def start_background_tasks(self):
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

    async def _heartbeat_monitor(self):
        while True:
            await asyncio.sleep(5)
            if self.client is not None:
                silent_for = time.monotonic() - self.last_seen_ping
                if silent_for > settings.heartbeat_timeout:
                    log.warning("Heartbeat timeout (%.0fs silent), dropping client", silent_for)
                    client = self.client
                    try:
                        await client.close(code=4408)
                    except Exception:
                        pass

    # ------------------------------------------------------------ client I/O

    async def handle_client(self, ws):
        await ws.accept()
        if self.client is not None:
            await ws.send_text(json.dumps({
                "type": "error",
                "message": "A session is already active in another tab.",
            }))
            await ws.close(code=4409)
            return
        if self.state == SessionState.SHUTTING_DOWN:
            await ws.send_text(json.dumps({
                "type": "error",
                "message": "Previous session is shutting down, retry in a moment.",
            }))
            await ws.close(code=4503)
            return

        self.client = ws
        self.last_seen_ping = time.monotonic()
        self._cancel_grace()

        try:
            if self.state == SessionState.DRAINING:
                # Reconnect during grace: resume the live session.
                self.state = SessionState.RUNNING
                await self._send_status()
                if self.capture:
                    self.capture.request_keyframe()
            elif self.state == SessionState.IDLE:
                await self._send_status()
                # Launch in the background: the receive loop must keep
                # servicing pings while Blender starts up.
                asyncio.create_task(self.launch())
            else:
                await self._send_status()
                if self.capture:
                    self.capture.request_keyframe()

            while True:
                raw = await ws.receive_text()
                self.last_seen_ping = time.monotonic()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                await self._handle_client_message(msg)
        except Exception:
            # WebSocketDisconnect and friends all land here.
            pass
        finally:
            if self.client is ws:
                self.client = None
                if self.injector:
                    self.injector.release_all()
                if self.state == SessionState.RUNNING:
                    self.state = SessionState.DRAINING
                    self._schedule_grace()

    async def _handle_client_message(self, msg: dict):
        kind = msg.get("type")
        if kind == "ping":
            await self._send_json({"type": "pong"})
        elif kind in INPUT_TYPES:
            if self.injector is not None:
                try:
                    self.injector.handle(msg)
                except Exception:
                    log.exception("Input injection failed")
        elif kind == "launch":
            if self.state == SessionState.IDLE:
                asyncio.create_task(self.launch())
        elif kind == "request_keyframe":
            if self.capture:
                self.capture.request_keyframe()

    async def _send_json(self, msg: dict):
        if self.client is None:
            return
        try:
            await self.client.send_text(json.dumps(msg))
        except Exception:
            pass

    async def _send_status(self, **extra):
        await self._send_json({"type": "status", "state": self.state.value, **extra})

    async def _on_frame(self, payload: bytes, keyframe: bool, pts_us: int):
        if self.client is None:
            return
        try:
            await self.client.send_bytes(FRAME_HEADER.pack(1 if keyframe else 0, pts_us) + payload)
        except Exception:
            pass

    # ----------------------------------------------------------------- launch

    async def launch(self):
        async with self._lock:
            if self.state not in (SessionState.IDLE,):
                return
            self.state = SessionState.LAUNCHING
            await self._send_status()
            try:
                await self._launch_inner()
                if self.client is None:
                    # Client vanished mid-launch: enter grace immediately so
                    # Blender can't linger without an owner.
                    self.state = SessionState.DRAINING
                    self._schedule_grace()
                else:
                    self.state = SessionState.RUNNING
                await self._send_status()
            except Exception as exc:
                log.exception("Launch failed")
                await self._send_json({"type": "error", "message": f"Launch failed: {exc}"})
                await self._cleanup_processes(force=True)
                self.state = SessionState.IDLE
                await self._send_status()

    async def _launch_inner(self):
        if sys.platform == "darwin" and not os.path.exists(settings.blender_path):
            raise RuntimeError(f"Blender not found at {settings.blender_path}")
        if not os.path.exists(settings.capture_helper_path):
            raise RuntimeError(
                f"Capture helper not built ({settings.capture_helper_path}). "
                "Run capture-helper/build.sh first."
            )

        self.channel = BlenderChannel()
        channel_port = await self.channel.start()

        args = [
            settings.blender_path,
            *settings.extra_blender_args,
            "--python", settings.bootstrap_script,
            "--", "--bsm-port", str(channel_port),
        ]
        log.info("Launching Blender: %s", " ".join(args))
        # start_new_session detaches Blender from our process group so terminal
        # signals to the manager don't bypass the graceful shutdown flow.
        self.blender_proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
        )
        self._exit_watch_task = asyncio.create_task(self._watch_blender_exit(self.blender_proc))

        try:
            await asyncio.wait_for(self.channel.connected.wait(), timeout=30)
        except asyncio.TimeoutError:
            log.warning("Blender bootstrap did not connect within 30s (continuing)")

        info = await wait_for_blender_window(self.blender_proc.pid, settings.window_wait_timeout)
        self.tracker = WindowTracker(self.blender_proc.pid, info)
        self.injector = InputInjector(self.blender_proc.pid, self.tracker)

        await self._start_capture(info)
        self._resize_task = asyncio.create_task(self._watch_resize())

    def _capture_size(self, info) -> tuple[int, int]:
        # Window bounds are in points; cap encoded width (Retina is 2x, and
        # full-res Retina encode wastes battery for little visual gain at
        # streaming sizes).
        width = min(settings.max_capture_width, int(info.width))
        height = int(round(width * info.height / max(info.width, 1)))
        return (width - width % 2, height - height % 2)

    async def _start_capture(self, info):
        width, height = self._capture_size(info)
        self._capture_started_at = time.monotonic()
        self.capture = CaptureProcess(
            helper_path=settings.capture_helper_path,
            window_id=info.window_id,
            width=width,
            height=height,
            fps=settings.fps,
            bitrate=settings.bitrate,
            on_frame=self._on_frame,
            on_exit=self._on_capture_exit,
        )
        await self.capture.start()

    async def _on_capture_exit(self):
        # Capture helper died while session is alive: try to restart it once
        # the window is still around (e.g. transient SCK error).
        if self.state not in (SessionState.RUNNING, SessionState.DRAINING):
            return
        if time.monotonic() - self._capture_started_at < 3:
            self._capture_failures += 1
        else:
            self._capture_failures = 1
        if self._capture_failures >= 5:
            log.error("Capture helper keeps crashing, giving up")
            await self._send_json({
                "type": "error",
                "message": (
                    "Screen capture keeps failing. Most likely the Screen Recording "
                    "permission is missing: System Settings -> Privacy & Security -> "
                    "Screen Recording -> enable your terminal app, then fully quit "
                    "and reopen it and restart the server."
                ),
            })
            return
        await asyncio.sleep(1)
        if self.state not in (SessionState.RUNNING, SessionState.DRAINING) or self.tracker is None:
            return
        info = self.tracker.refresh()
        if info is None:
            return
        log.info("Restarting capture helper")
        await self._start_capture(info)
        await self._send_json({"type": "stream_restart"})

    async def _watch_resize(self):
        """Restart capture when the Blender window is resized (the encoded
        aspect ratio must track the window or input mapping skews)."""
        try:
            while self.state in (SessionState.RUNNING, SessionState.DRAINING, SessionState.LAUNCHING):
                await asyncio.sleep(2)
                if self.tracker is None or self.capture is None:
                    continue
                before = self.tracker.info
                after = await asyncio.to_thread(self.tracker.refresh)
                if after is None:
                    continue
                dw = abs(after.width - before.width) / max(before.width, 1)
                dh = abs(after.height - before.height) / max(before.height, 1)
                if dw > 0.02 or dh > 0.02:
                    log.info("Window resized %s -> %s, restarting capture",
                             before.bounds, after.bounds)
                    await self.capture.stop()
                    await self._start_capture(after)
                    await self._send_json({"type": "stream_restart"})
        except asyncio.CancelledError:
            pass

    async def _watch_blender_exit(self, proc: asyncio.subprocess.Process):
        code = await proc.wait()
        if self.blender_proc is not proc:
            return
        log.info("Blender exited with code %s", code)
        if self.state != SessionState.SHUTTING_DOWN:
            # Blender quit on its own (File > Quit inside the stream).
            await self._cleanup_processes(force=False)
            self.state = SessionState.IDLE
            self._cancel_grace()
            await self._send_json({"type": "blender_exited"})
            await self._send_status()

    # --------------------------------------------------------------- shutdown

    def _schedule_grace(self):
        self._cancel_grace()
        self._grace_task = asyncio.create_task(self._grace_countdown())

    def _cancel_grace(self):
        if self._grace_task is not None:
            self._grace_task.cancel()
            self._grace_task = None

    async def _grace_countdown(self):
        try:
            await asyncio.sleep(settings.disconnect_grace)
        except asyncio.CancelledError:
            return
        if self.client is None and self.state == SessionState.DRAINING:
            log.info("Disconnect grace expired, shutting down Blender")
            await self.shutdown(reason="client_disconnected")

    async def shutdown(self, reason: str, immediate: bool = False):
        async with self._lock:
            if self.state in (SessionState.IDLE, SessionState.SHUTTING_DOWN):
                return
            self.state = SessionState.SHUTTING_DOWN
            await self._send_status()

            if self.capture:
                await self.capture.stop()
                self.capture = None

            proc = self.blender_proc
            if proc is not None and proc.returncode is None and self.channel is not None:
                ack_timeout = 3 if immediate else settings.shutdown_ack_timeout
                log.info("Sending shutdown_request (reason=%s)", reason)
                ack = await self.channel.request_shutdown(reason, timeout=ack_timeout)
                if ack == "saved":
                    log.info("Blender confirmed save")
                else:
                    log.warning("No save confirmation from Blender (ack=%s)", ack)

                try:
                    await asyncio.wait_for(proc.wait(), timeout=settings.exit_wait_timeout)
                    log.info("Blender exited cleanly")
                except asyncio.TimeoutError:
                    log.warning("Blender still running, sending SIGTERM")
                    self._signal_blender(proc, signal.SIGTERM)
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        log.error("Blender unresponsive, sending SIGKILL")
                        self._signal_blender(proc, signal.SIGKILL)
                        await proc.wait()

            await self._cleanup_processes(force=False)
            self.state = SessionState.IDLE
            await self._send_status()

    @staticmethod
    def _signal_blender(proc: asyncio.subprocess.Process, sig: int):
        try:
            proc.send_signal(sig)
        except ProcessLookupError:
            pass

    async def _cleanup_processes(self, force: bool):
        if self._resize_task is not None:
            self._resize_task.cancel()
            self._resize_task = None
        if self.capture is not None:
            await self.capture.stop()
            self.capture = None
        if self.channel is not None:
            await self.channel.stop()
            self.channel = None
        if force and self.blender_proc is not None and self.blender_proc.returncode is None:
            self._signal_blender(self.blender_proc, signal.SIGKILL)
        self.blender_proc = None
        self.tracker = None
        self.injector = None
