"""Blender stream session manager.

FastAPI server (127.0.0.1 only) that:
  - serves the built React frontend,
  - exposes /session, the single WebSocket carrying video out and input in,
  - owns the Blender process lifecycle (launch, heartbeat, graceful shutdown).

Run:  python main.py   (or: uvicorn main:app --host 127.0.0.1 --port 8765)
"""

import logging
import os
import secrets
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from session import StreamSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
log = logging.getLogger("main")

# Per-run token: pages from other origins can open ws://localhost sockets
# (CORS does not gate WebSockets), so the frontend must fetch this token
# same-origin before connecting.
TOKEN = secrets.token_urlsafe(24)

session = StreamSession()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if sys.platform != "darwin":
        log.warning("Not running on macOS: capture and input injection are disabled stubs.")
    await session.start_background_tasks()
    yield
    await session.shutdown(reason="server_exit", immediate=True)


app = FastAPI(lifespan=lifespan)


@app.get("/api/config")
async def api_config():
    return {"token": TOKEN, "fps": settings.fps}


@app.websocket("/session")
async def ws_session(ws: WebSocket):
    if ws.query_params.get("token") != TOKEN:
        await ws.close(code=4401)
        return
    await session.handle_client(ws)


if os.path.isdir(settings.frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(settings.frontend_dist, "assets")), name="assets")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(settings.frontend_dist, "index.html"))
else:
    @app.get("/")
    async def index_missing():
        return JSONResponse(
            {"error": "Frontend not built. Run: cd frontend && npm install && npm run build"},
            status_code=503,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
