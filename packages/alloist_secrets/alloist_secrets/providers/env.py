"""Environment variable provider. Supports .env file via python-dotenv."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if it exists (only if not already set - dotenv won't override)
_load_done = False


def _ensure_loaded() -> None:
    global _load_done
    if _load_done:
        return
    _load_done = True
    # Try common locations
    for path in [Path.cwd() / ".env", Path(__file__).resolve().parents[3] / ".env"]:
        if path.exists():
            load_dotenv(path)
            break


def get(key: str) -> str | None:
    """Get secret from environment. Returns None if not set or empty."""
    _ensure_loaded()
    val = os.environ.get(key)
    if val is None or val.strip() == "":
        return None
    return val
