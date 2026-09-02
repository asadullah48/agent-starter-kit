"""Logging setup shared by the CLI and the API.

Logs to both the console and logs/app.log so `logs/` actually fills up
during development instead of being an empty folder in the repo.
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

    _LOG_DIR.mkdir(exist_ok=True)
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(_LOG_DIR / "app.log", encoding="utf-8"),
        ],
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
