# Blender Stream — local Blender in your browser tab (macOS, Apple Silicon)

Stream a **full, native Blender session** into a browser tab and control it with
the exact same keybinds — like GeForce Now / Shadow PC, but for your own Mac.
Blender runs as a normal local process; the browser is just a low-latency
remote display + input device for it.

- **Full UI**: the entire Blender window is streamed (menus, panels, splash
  screen, recent-files gateway — everything native, nothing custom).
- **60 fps hardware pipeline**: ScreenCaptureKit window capture → VideoToolbox
  H.264 encode (Apple hardware encoder) → WebSocket → WebCodecs hardware
  decode in the browser. No CPU encoding loops, battery friendly on M1.
- **Native input**: browser mouse/keyboard events are injected directly into
  the Blender *process* (`CGEventPostToPid`), so Blender's default keymap
  (G/R/S, numpad views, Tab, middle-mouse orbit…) works unchanged.
- **Graceful lifecycle**: closing the tab saves your project (Cmd+S
  equivalent) and exits Blender cleanly. No orphaned processes — in either
  direction.

## Requirements

- macOS 13+ (Sonoma recommended), Apple Silicon (built for M1 Air)
- [Blender 4.x](https://www.blender.org/download/) (Apple Silicon build) at
  `/Applications/Blender.app`
- Python 3.10+
- Node.js 18+ (only to build the frontend)
- Xcode Command Line Tools (`xcode-select --install`) to build the capture helper
- A WebCodecs-capable browser: Chrome / Arc / Edge (recommended), Safari 16.4+

## Setup

```bash
# 1. Build the Swift capture helper (ScreenCaptureKit + VideoToolbox)
./capture-helper/build.sh

# 2. Build the frontend
cd frontend && npm install && npm run build && cd ..

# 3. Install backend dependencies
python3 -m pip install -r backend/session-manager/requirements.txt
```

### Grant macOS permissions (one time)

Both permissions go to **the app you run the server from** (e.g. Terminal,
iTerm, or your IDE), under **System Settings → Privacy & Security**:

1. **Screen Recording** — required by the capture helper. macOS will prompt on
   first run; approve and restart the server.
2. **Accessibility** — required for input injection (`CGEventPostToPid`).
   Add your terminal app manually if you aren't prompted.

## Run

```bash
python3 backend/session-manager/main.py
```

Open **http://127.0.0.1:8765** in Chrome/Arc. That's it:

1. The tab connects → the session manager launches Blender (normal launch,
   including the splash screen with your recent projects).
2. The Blender window is captured and streamed at up to 60 fps.
3. Your mouse/keyboard in the tab controls Blender natively.
4. Close the tab → after a 10 s grace period (page refreshes survive),
   Blender **saves** and exits cleanly. Files that were never saved go to
   `~/Library/Application Support/blender_stream/session_autosave_<ts>.blend`
   and appear in Recent Files next launch.

Click **Fullscreen** in the status bar to enable keyboard lock (Chromium
only): browser-reserved shortcuts like **Cmd+W** then reach Blender instead
of closing the tab.

## Configuration (environment variables)

| Variable | Default | Meaning |
| --- | --- | --- |
| `BSM_PORT` | `8765` | HTTP/WebSocket port (bound to 127.0.0.1) |
| `BSM_BLENDER_PATH` | `/Applications/Blender.app/Contents/MacOS/Blender` | Blender binary |
| `BSM_FPS` | `60` | Capture/encode frame rate |
| `BSM_MAX_WIDTH` | `1280` | Encoded stream width cap (height follows window aspect) |
| `BSM_BITRATE` | `8000000` | H.264 bitrate (bits/s) |
| `BSM_DISCONNECT_GRACE` | `10` | Seconds to keep Blender alive after tab disconnect |
| `BSM_HEARTBEAT_TIMEOUT` | `20` | Seconds without a ping before the client is dropped |
| `BSM_BLENDER_ARGS` | _(empty)_ | Extra args passed to Blender |

## How it works

```
┌────────────┐   H.264 / WebCodecs   ┌──────────────────┐  Annex B  ┌──────────────────┐
│  Browser    │◄─────────────────────│  Session Manager  │◄──────────│ blender-capture   │
│  (React)    │   input JSON (WS)    │  (FastAPI)        │  stdout   │ (Swift: SCK + VT) │
└────────────┘──────────────────────►└──────────────────┘           └──────────────────┘
                                       │           │  CGEventPostToPid       ▲ captures window
                                       │           ▼                         │
                                       │  JSON-lines TCP        ┌────────────┴───┐
                                       └───────────────────────►│  Blender 4.x    │
                                          (lifecycle channel)   │  + bootstrap.py │
                                                                └────────────────┘
```

- **Capture** (`capture-helper/main.swift`): per-window, desktop-independent
  capture — streaming continues even when Blender is behind other windows.
  Low-latency VideoToolbox H.264 (no B-frames, in-band SPS/PPS) framed onto
  stdout; the manager relays frames to the browser untouched.
- **Input** (`input_injector.py`): since browser and Blender share the same
  Mac, events are posted *to the Blender process*, not the global event tap —
  global injection would land in the focused app (the browser itself).
  Physical-key mapping (`KeyboardEvent.code` → macOS virtual keycodes)
  preserves Blender's keymap exactly; drags, double-clicks, scroll momentum
  and modifier combos are synthesized faithfully.
- **Lifecycle** (`blender-addon/bootstrap.py`): injected via `--python` at
  launch, zero install, stdlib only. Handles `shutdown_request` → save →
  `shutdown_ack` → `bpy.ops.wm.quit_blender()`. If the manager itself dies,
  the dropped socket triggers the same save-and-exit, so Blender never
  lingers as a ghost. The manager backstops with SIGTERM → SIGKILL.
- **Session state machine** (`session.py`):
  `IDLE → LAUNCHING → RUNNING ⇄ DRAINING → SHUTTING_DOWN → IDLE`, with
  heartbeat (5 s ping / 20 s timeout), reconnect-during-grace, window-resize
  capture restarts, and a relaunch flow when Blender is quit from inside the
  stream.

## Limitations & notes

- **Blender's window stays on your Mac.** This is a local stream, not
  virtualization — the window must exist (it can sit behind other windows,
  but don't minimize it to the Dock: ScreenCaptureKit stops delivering frames
  for minimized windows).
- **Browser-reserved shortcuts** (Cmd+W, Cmd+T, Cmd+N, Cmd+Q) only reach
  Blender in fullscreen with keyboard lock (Chromium). Outside fullscreen the
  browser handles them — Cmd+W will close the tab (which safely saves and
  shuts Blender down, by design).
- **One session, one tab.** A second tab is rejected while the first is
  connected.
- Window dragging/resizing through the stream works, but the stream restarts
  (~1 s hiccup) after a resize so the encoded aspect ratio tracks the window.
- `CGEventPostToPid` delivers events regardless of focus; if you find some
  interaction requires Blender to be frontmost, report it — a fallback that
  activates the app on click can be added.
- Audio is not streamed.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Black/no video, helper exits | Grant **Screen Recording** to your terminal, restart the server |
| Video works, input does nothing | Grant **Accessibility** to your terminal |
| `Capture helper not built` | Run `./capture-helper/build.sh` (needs Xcode CLT) |
| `Blender not found` | Set `BSM_BLENDER_PATH` |
| Choppy stream | Lower `BSM_FPS` to 30 or `BSM_MAX_WIDTH` to 960 |
| Stale Blender after a crash | The bootstrap exits when its socket drops; if you SIGKILL'd everything at once: `pkill -f Blender` |

## Project structure

```
backend/session-manager/
  main.py             FastAPI app: token auth, WS endpoint, static frontend
  session.py          Session state machine, lifecycle, shutdown flow
  capture.py          Capture helper subprocess + frame relay
  input_injector.py   CGEventPostToPid mouse/keyboard/scroll synthesis
  keymap.py           KeyboardEvent.code -> macOS virtual keycodes
  window_tracker.py   Blender window discovery + bounds tracking
  blender_channel.py  JSON-lines TCP lifecycle channel to Blender
  config.py           Env-overridable settings
capture-helper/
  main.swift          ScreenCaptureKit -> VideoToolbox H.264 -> stdout
  build.sh
blender-addon/
  bootstrap.py        In-Blender lifecycle client (save-on-shutdown)
frontend/
  src/App.jsx         Status bar, overlays, heartbeat, fullscreen+keylock
  src/Viewport.jsx    WebCodecs decoder -> canvas
  src/input.js        Input capture/forwarding (preventDefault, pointer capture)
  src/ws.js           WebSocket client with reconnect/backoff
```
