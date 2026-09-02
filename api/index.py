"""Vercel entrypoint -- re-exports the FastAPI app from src/api/app.py.

Separate from `main.py` (the local CLI/uvicorn entrypoint): Vercel's
Python runtime looks for a module-level `app` object in a file under
`api/`. See vercel.json for the function config.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from api.app import app  # noqa: E402
