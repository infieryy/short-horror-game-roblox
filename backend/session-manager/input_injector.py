"""Inject browser input into the Blender process via Quartz CGEvents.

Because the browser and Blender run on the SAME Mac, events must be posted
directly to the Blender process (CGEventPostToPid) rather than to the global
HID event tap -- global injection would land in whatever app has focus
(usually the browser itself, creating a feedback loop).

Requires the Accessibility permission for the process running this server
(System Settings -> Privacy & Security -> Accessibility -> your terminal).
"""

import logging
import sys
import time
from typing import Optional

from keymap import JS_CODE_TO_MAC_KEYCODE
from window_tracker import WindowTracker

log = logging.getLogger(__name__)

IS_MACOS = sys.platform == "darwin"

if IS_MACOS:
    from Quartz import (  # type: ignore
        CGEventCreateKeyboardEvent,
        CGEventCreateMouseEvent,
        CGEventCreateScrollWheelEvent,
        CGEventPostToPid,
        CGEventSetFlags,
        CGEventSetIntegerValueField,
        CGEventSetLocation,
        kCGEventFlagMaskAlternate,
        kCGEventFlagMaskCommand,
        kCGEventFlagMaskControl,
        kCGEventFlagMaskShift,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseDragged,
        kCGEventLeftMouseUp,
        kCGEventMouseMoved,
        kCGEventOtherMouseDown,
        kCGEventOtherMouseDragged,
        kCGEventOtherMouseUp,
        kCGEventRightMouseDown,
        kCGEventRightMouseDragged,
        kCGEventRightMouseUp,
        kCGMouseButtonCenter,
        kCGMouseButtonLeft,
        kCGMouseButtonRight,
        kCGMouseEventClickState,
        kCGMouseEventDeltaX,
        kCGMouseEventDeltaY,
        kCGScrollEventUnitPixel,
    )

    # browser e.button -> (mac button constant, down, up, dragged)
    _BUTTON_TABLE = {
        0: (kCGMouseButtonLeft, kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventLeftMouseDragged),
        1: (kCGMouseButtonCenter, kCGEventOtherMouseDown, kCGEventOtherMouseUp, kCGEventOtherMouseDragged),
        2: (kCGMouseButtonRight, kCGEventRightMouseDown, kCGEventRightMouseUp, kCGEventRightMouseDragged),
    }

DOUBLE_CLICK_SECONDS = 0.4
DOUBLE_CLICK_RADIUS = 6.0


class InputInjector:
    def __init__(self, pid: int, tracker: WindowTracker):
        self.pid = pid
        self.tracker = tracker
        self.pressed_buttons: set[int] = set()
        self.last_pos = (0.0, 0.0)
        self._last_click_time: dict[int, float] = {}
        self._last_click_pos: dict[int, tuple[float, float]] = {}
        self._click_state: dict[int, int] = {}
        self._flags = 0

    # ------------------------------------------------------------------ utils

    def _to_screen(self, nx: float, ny: float) -> tuple[float, float]:
        """Map normalized video coords (0..1) to global screen coords inside
        the Blender window. The capture covers the full window frame, and the
        CGWindowList bounds describe the same frame, so this is a direct map."""
        info = self.tracker.current()
        nx = min(max(nx, 0.0), 1.0)
        ny = min(max(ny, 0.0), 1.0)
        return (info.x + nx * info.width, info.y + ny * info.height)

    def _update_flags(self, modifiers: Optional[dict]):
        if modifiers is None:
            return
        flags = 0
        if modifiers.get("shift"):
            flags |= kCGEventFlagMaskShift
        if modifiers.get("ctrl"):
            flags |= kCGEventFlagMaskControl
        if modifiers.get("alt"):
            flags |= kCGEventFlagMaskAlternate
        if modifiers.get("meta"):
            flags |= kCGEventFlagMaskCommand
        self._flags = flags

    def _post(self, event):
        CGEventSetFlags(event, self._flags)
        CGEventPostToPid(self.pid, event)

    # ---------------------------------------------------------------- dispatch

    def handle(self, msg: dict):
        if not IS_MACOS:
            return
        kind = msg.get("type")
        self._update_flags(msg.get("modifiers"))
        if kind == "mouse_move":
            self._mouse_move(msg)
        elif kind == "mouse_down":
            self._mouse_button(msg, down=True)
        elif kind == "mouse_up":
            self._mouse_button(msg, down=False)
        elif kind == "wheel":
            self._wheel(msg)
        elif kind == "key_down":
            self._key(msg, down=True)
        elif kind == "key_up":
            self._key(msg, down=False)

    # ------------------------------------------------------------------ mouse

    def _mouse_move(self, msg: dict):
        x, y = self._to_screen(float(msg.get("x", 0)), float(msg.get("y", 0)))
        dx, dy = x - self.last_pos[0], y - self.last_pos[1]
        self.last_pos = (x, y)

        if self.pressed_buttons:
            # Dragging: use the dragged event type for the first held button.
            btn = sorted(self.pressed_buttons)[0]
            mac_button, _, _, dragged = _BUTTON_TABLE[btn]
            event = CGEventCreateMouseEvent(None, dragged, (x, y), mac_button)
        else:
            event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), kCGMouseButtonLeft)
        CGEventSetIntegerValueField(event, kCGMouseEventDeltaX, int(round(dx)))
        CGEventSetIntegerValueField(event, kCGMouseEventDeltaY, int(round(dy)))
        self._post(event)

    def _mouse_button(self, msg: dict, down: bool):
        btn = int(msg.get("button", 0))
        if btn not in _BUTTON_TABLE:
            return
        x, y = self._to_screen(float(msg.get("x", 0)), float(msg.get("y", 0)))
        self.last_pos = (x, y)
        mac_button, down_type, up_type, _ = _BUTTON_TABLE[btn]

        if down:
            now = time.monotonic()
            last_t = self._last_click_time.get(btn, 0.0)
            lx, ly = self._last_click_pos.get(btn, (-1e9, -1e9))
            near = abs(x - lx) <= DOUBLE_CLICK_RADIUS and abs(y - ly) <= DOUBLE_CLICK_RADIUS
            if now - last_t <= DOUBLE_CLICK_SECONDS and near:
                self._click_state[btn] = self._click_state.get(btn, 1) + 1
            else:
                self._click_state[btn] = 1
            self._last_click_time[btn] = now
            self._last_click_pos[btn] = (x, y)
            self.pressed_buttons.add(btn)
            event = CGEventCreateMouseEvent(None, down_type, (x, y), mac_button)
        else:
            self.pressed_buttons.discard(btn)
            event = CGEventCreateMouseEvent(None, up_type, (x, y), mac_button)

        CGEventSetIntegerValueField(event, kCGMouseEventClickState, self._click_state.get(btn, 1))
        self._post(event)

    def _wheel(self, msg: dict):
        x, y = self._to_screen(float(msg.get("x", 0)), float(msg.get("y", 0)))
        # Browser deltaY > 0 means scroll down; CGEvent wheel1 > 0 means scroll up.
        dy = int(round(-float(msg.get("dy", 0))))
        dx = int(round(-float(msg.get("dx", 0))))
        if dy == 0 and dx == 0:
            return
        event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitPixel, 2, dy, dx)
        CGEventSetLocation(event, (x, y))
        self._post(event)

    # --------------------------------------------------------------- keyboard

    def _key(self, msg: dict, down: bool):
        code = msg.get("code", "")
        keycode = JS_CODE_TO_MAC_KEYCODE.get(code)
        if keycode is None:
            log.debug("Unmapped key code: %s", code)
            return
        event = CGEventCreateKeyboardEvent(None, keycode, down)
        self._post(event)

    # ---------------------------------------------------------------- cleanup

    def release_all(self):
        """Release any held buttons (e.g. browser disconnected mid-drag)."""
        if not IS_MACOS:
            return
        for btn in list(self.pressed_buttons):
            mac_button, _, up_type, _ = _BUTTON_TABLE[btn]
            event = CGEventCreateMouseEvent(None, up_type, self.last_pos, mac_button)
            self._post(event)
        self.pressed_buttons.clear()
        self._flags = 0
