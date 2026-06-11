"""Manage the Swift capture helper subprocess and parse its frame stream.

Helper stdout framing:
    [u32 BE payload_len][u8 flags (bit0 = keyframe)][u64 BE pts_us][payload]
"""

import asyncio
import logging
import struct
from typing import Awaitable, Callable, Optional

log = logging.getLogger(__name__)

HEADER = struct.Struct(">IBQ")  # length, flags, pts_us

FrameCallback = Callable[[bytes, bool, int], Awaitable[None]]


class CaptureProcess:
    def __init__(
        self,
        helper_path: str,
        window_id: int,
        width: int,
        height: int,
        fps: int,
        bitrate: int,
        on_frame: FrameCallback,
        on_exit: Callable[[], Awaitable[None]],
    ):
        self.helper_path = helper_path
        self.window_id = window_id
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.on_frame = on_frame
        self.on_exit = on_exit
        self.proc: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._stopping = False

    async def start(self):
        args = [
            self.helper_path,
            "--window-id", str(self.window_id),
            "--width", str(self.width),
            "--height", str(self.height),
            "--fps", str(self.fps),
            "--bitrate", str(self.bitrate),
        ]
        log.info("Starting capture helper: %s", " ".join(args))
        self.proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader_task = asyncio.create_task(self._read_frames())
        asyncio.create_task(self._drain_stderr())

    async def _read_frames(self):
        assert self.proc and self.proc.stdout
        stdout = self.proc.stdout
        frames = 0
        try:
            while True:
                header = await stdout.readexactly(HEADER.size)
                length, flags, pts_us = HEADER.unpack(header)
                payload = await stdout.readexactly(length)
                frames += 1
                if frames == 1:
                    log.info("First video frame from helper (%d bytes, key=%s)", length, bool(flags & 1))
                elif frames % 600 == 0:
                    log.info("Relayed %d frames (last %d bytes)", frames, length)
                await self.on_frame(payload, bool(flags & 1), pts_us)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Capture frame reader failed")
        finally:
            if not self._stopping:
                log.warning("Capture helper exited unexpectedly")
                await self.on_exit()

    async def _drain_stderr(self):
        assert self.proc and self.proc.stderr
        try:
            async for line in self.proc.stderr:
                log.info("[capture] %s", line.decode(errors="replace").rstrip())
        except Exception:
            pass

    def request_keyframe(self):
        if self.proc and self.proc.stdin and not self.proc.stdin.is_closing():
            try:
                self.proc.stdin.write(b"keyframe\n")
            except (BrokenPipeError, ConnectionResetError):
                pass

    async def stop(self):
        self._stopping = True
        if self._reader_task:
            self._reader_task.cancel()
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                try:
                    self.proc.kill()
                except ProcessLookupError:
                    pass
        self.proc = None
