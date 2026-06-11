"""Configuration for the Blender stream session manager (env-overridable)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass
class Settings:
    host: str = os.environ.get("BSM_HOST", "127.0.0.1")
    port: int = _env_int("BSM_PORT", 8765)

    # Apple Silicon Blender binary.
    blender_path: str = os.environ.get(
        "BSM_BLENDER_PATH", "/Applications/Blender.app/Contents/MacOS/Blender"
    )

    # Compiled Swift capture helper.
    capture_helper_path: str = os.environ.get(
        "BSM_CAPTURE_HELPER", str(REPO_ROOT / "capture-helper" / "blender-capture")
    )

    bootstrap_script: str = os.environ.get(
        "BSM_BOOTSTRAP", str(REPO_ROOT / "blender-addon" / "bootstrap.py")
    )

    frontend_dist: str = os.environ.get(
        "BSM_FRONTEND_DIST", str(REPO_ROOT / "frontend" / "dist")
    )

    # Streaming.
    fps: int = _env_int("BSM_FPS", 60)
    max_capture_width: int = _env_int("BSM_MAX_WIDTH", 1280)
    bitrate: int = _env_int("BSM_BITRATE", 8_000_000)

    # Lifecycle timing (seconds).
    heartbeat_timeout: float = float(os.environ.get("BSM_HEARTBEAT_TIMEOUT", 20))
    disconnect_grace: float = float(os.environ.get("BSM_DISCONNECT_GRACE", 10))
    shutdown_ack_timeout: float = float(os.environ.get("BSM_ACK_TIMEOUT", 10))
    exit_wait_timeout: float = float(os.environ.get("BSM_EXIT_TIMEOUT", 10))
    window_wait_timeout: float = float(os.environ.get("BSM_WINDOW_TIMEOUT", 60))

    extra_blender_args: list = field(
        default_factory=lambda: [
            a for a in os.environ.get("BSM_BLENDER_ARGS", "").split() if a
        ]
    )


settings = Settings()
