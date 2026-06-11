"""Locate and track the Blender window via the CoreGraphics window list."""

import asyncio
import logging
import sys
import time
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

IS_MACOS = sys.platform == "darwin"

if IS_MACOS:
    from Quartz import (  # type: ignore
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListExcludeDesktopElements,
        kCGWindowListOptionAll,
    )


@dataclass
class WindowInfo:
    window_id: int
    x: float
    y: float
    width: float
    height: float

    @property
    def bounds(self):
        return (self.x, self.y, self.width, self.height)


def find_blender_window(pid: int) -> Optional[WindowInfo]:
    """Find the main (largest, layer-0) window owned by `pid`.

    Coordinates are in global display space, origin at the top-left of the
    main display with y increasing downward -- the same space CGEvent uses.
    """
    if not IS_MACOS:
        return None

    options = kCGWindowListOptionAll | kCGWindowListExcludeDesktopElements
    windows = CGWindowListCopyWindowInfo(options, kCGNullWindowID) or []

    best: Optional[WindowInfo] = None
    best_area = 0.0
    for w in windows:
        if int(w.get("kCGWindowOwnerPID", -1)) != pid:
            continue
        if int(w.get("kCGWindowLayer", 0)) != 0:
            continue
        bounds = w.get("kCGWindowBounds") or {}
        width = float(bounds.get("Width", 0))
        height = float(bounds.get("Height", 0))
        area = width * height
        # Ignore tiny utility windows / tooltips.
        if area < 200 * 200:
            continue
        if area > best_area:
            best_area = area
            best = WindowInfo(
                window_id=int(w.get("kCGWindowNumber", 0)),
                x=float(bounds.get("X", 0)),
                y=float(bounds.get("Y", 0)),
                width=width,
                height=height,
            )
    return best


async def wait_for_blender_window(pid: int, timeout: float) -> WindowInfo:
    """Poll until Blender's main window appears (it takes a moment after spawn)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        info = await asyncio.to_thread(find_blender_window, pid)
        if info is not None:
            log.info("Found Blender window id=%s bounds=%s", info.window_id, info.bounds)
            return info
        await asyncio.sleep(0.25)
    raise TimeoutError(f"Blender window for pid {pid} did not appear within {timeout}s")


class WindowTracker:
    """Caches Blender window bounds, refreshing at most every `refresh_interval`."""

    def __init__(self, pid: int, initial: WindowInfo, refresh_interval: float = 0.5):
        self.pid = pid
        self.info = initial
        self.refresh_interval = refresh_interval
        self._last_refresh = time.monotonic()

    def current(self) -> WindowInfo:
        now = time.monotonic()
        if now - self._last_refresh >= self.refresh_interval:
            self._last_refresh = now
            fresh = find_blender_window(self.pid)
            if fresh is not None:
                self.info = fresh
        return self.info

    def refresh(self) -> Optional[WindowInfo]:
        fresh = find_blender_window(self.pid)
        if fresh is not None:
            self.info = fresh
            self._last_refresh = time.monotonic()
        return fresh
