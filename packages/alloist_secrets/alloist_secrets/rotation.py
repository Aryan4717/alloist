"""Background secret rotation - periodic refresh from AWS/Vault."""

import os
import threading
import time

from alloist_secrets.loader import _CACHE_LOCK, _PROVIDER_SOURCE, refresh_key


_rotation_thread: threading.Thread | None = None
_rotation_stop = threading.Event()


def _rotation_loop(interval_sec: int) -> None:
    """Background loop that refreshes non-env secrets."""
    while not _rotation_stop.wait(interval_sec):
        try:
            keys_to_refresh = [
                k for k, s in _PROVIDER_SOURCE.items()
                if s in ("aws", "vault")
            ]
            for key in keys_to_refresh:
                try:
                    refresh_key(key)
                except Exception:
                    pass
        except Exception:
            pass


def start_rotation(interval_sec: int | None = None) -> None:
    """Start background rotation if SECRET_REFRESH_INTERVAL_SEC is set."""
    global _rotation_thread
    if _rotation_thread is not None:
        return
    interval = interval_sec
    if interval is None:
        try:
            interval = int(os.environ.get("SECRET_REFRESH_INTERVAL_SEC", "0"))
        except ValueError:
            interval = 0
    if interval <= 0:
        return
    _rotation_stop.clear()
    _rotation_thread = threading.Thread(
        target=_rotation_loop,
        args=(interval,),
        daemon=True,
    )
    _rotation_thread.start()


def stop_rotation() -> None:
    """Stop the rotation thread."""
    global _rotation_thread
    _rotation_stop.set()
    if _rotation_thread:
        _rotation_thread.join(timeout=5)
        _rotation_thread = None
