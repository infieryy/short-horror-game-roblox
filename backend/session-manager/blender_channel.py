"""Lifecycle channel between the session manager and the Blender bootstrap.

A plain JSON-lines-over-TCP socket on 127.0.0.1 (random port) is used instead
of WebSocket so the in-Blender side needs nothing beyond the Python stdlib --
no packages installed into Blender's bundled Python.
"""

import asyncio
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


class BlenderChannel:
    """TCP server accepting a single connection from the Blender bootstrap."""

    def __init__(self):
        self.server: Optional[asyncio.AbstractServer] = None
        self.port: int = 0
        self._writer: Optional[asyncio.StreamWriter] = None
        self.connected = asyncio.Event()
        self.shutdown_ack = asyncio.Event()
        self.ack_status: Optional[str] = None

    async def start(self) -> int:
        self.server = await asyncio.start_server(
            self._handle_connection, host="127.0.0.1", port=0
        )
        self.port = self.server.sockets[0].getsockname()[1]
        log.info("Blender lifecycle channel listening on 127.0.0.1:%d", self.port)
        return self.port

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if self._writer is not None:
            log.warning("Second Blender channel connection rejected")
            writer.close()
            return
        self._writer = writer
        log.info("Blender bootstrap connected to lifecycle channel")
        self.connected.set()
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                await self._handle_message(msg)
        except (ConnectionResetError, asyncio.IncompleteReadError):
            pass
        finally:
            log.info("Blender bootstrap disconnected from lifecycle channel")
            self._writer = None
            self.connected.clear()

    async def _handle_message(self, msg: dict):
        kind = msg.get("type")
        if kind == "hello":
            log.info("Blender bootstrap hello: pid=%s blender=%s", msg.get("pid"), msg.get("blender_version"))
        elif kind == "shutdown_ack":
            self.ack_status = msg.get("status", "unknown")
            log.info("Received shutdown_ack: status=%s path=%s", self.ack_status, msg.get("path"))
            self.shutdown_ack.set()
        elif kind == "ping":
            await self.send({"type": "pong"})

    async def send(self, msg: dict) -> bool:
        if self._writer is None or self._writer.is_closing():
            return False
        try:
            self._writer.write((json.dumps(msg) + "\n").encode())
            await self._writer.drain()
            return True
        except (ConnectionResetError, BrokenPipeError):
            return False

    async def request_shutdown(self, reason: str, timeout: float) -> Optional[str]:
        """Send shutdown_request and wait for shutdown_ack. Returns ack status
        or None on timeout / no connection."""
        self.shutdown_ack.clear()
        self.ack_status = None
        if not await self.send({"type": "shutdown_request", "reason": reason}):
            return None
        try:
            await asyncio.wait_for(self.shutdown_ack.wait(), timeout=timeout)
            return self.ack_status
        except asyncio.TimeoutError:
            return None

    async def stop(self):
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        self.connected.clear()
