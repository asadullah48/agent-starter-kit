"""Logging setup shared by the CLI and the API.

Logs to both the console and logs/app.log during local development. On a
read-only deployment filesystem (e.g. a serverless platform like Vercel,
where only /tmp is writable) the file handler is skipped instead of
crashing the whole app on import -- console logging still works there.
"""

from __future__ import annotations

import logging
from pathlib import Path

from utils.config import get_settings

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    settings = get_settings()
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    try:
        _LOG_DIR.mkdir(exist_ok=True)
        handlers.append(logging.FileHandler(_LOG_DIR / "app.log", encoding="utf-8"))
    except OSError:
        # Read-only filesystem -- fall back to console-only logging.
        pass

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        handlers=handlers,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
