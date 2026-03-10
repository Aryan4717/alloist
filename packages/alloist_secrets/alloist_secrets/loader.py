"""Secret loader with cascade: env -> AWS -> Vault."""

import os
import threading
from typing import Callable

from alloist_secrets.providers import aws, env, vault

_CACHE: dict[str, str | None] = {}
_CACHE_LOCK = threading.Lock()
_PROVIDER_SOURCE: dict[str, str] = {}  # key -> "env" | "aws" | "vault"


def _fetch(key: str) -> tuple[str | None, str]:
    """Fetch from providers in cascade order. Returns (value, provider_name)."""
    # 1. Env
    val = env.get(key)
    if val is not None:
        return (val, "env")

    # 2. AWS
    if os.environ.get("SECRET_PROVIDER_AWS", "").lower() in ("1", "true", "yes"):
        val = aws.get(key)
        if val is not None:
            return (val, "aws")

    # 3. Vault
    if os.environ.get("SECRET_PROVIDER_VAULT", "").lower() in ("1", "true", "yes"):
        val = vault.get(key)
        if val is not None:
            return (val, "vault")

    return (None, "")


def get(key: str, default: str | None = None) -> str | None:
    """
    Get secret. Cascade: env -> AWS -> Vault.
    Returns default if not found and default is provided, else None.
    """
    with _CACHE_LOCK:
        if key in _CACHE:
            val = _CACHE[key]
            return val if val is not None else default

        val, source = _fetch(key)
        _CACHE[key] = val
        if source:
            _PROVIDER_SOURCE[key] = source
        if val is None and default is not None:
            return default
        return val if val is not None else default


def get_required(key: str) -> str:
    """Get secret; raise MissingSecretError if not found."""
    val = get(key)
    if val is None or val.strip() == "":
        from alloist_secrets import MissingSecretError

        raise MissingSecretError(key)
    return val


def refresh_key(key: str) -> None:
    """Refresh a single key from its source provider."""
    source = _PROVIDER_SOURCE.get(key, "")
    with _CACHE_LOCK:
        _CACHE.pop(key, None)
        _PROVIDER_SOURCE.pop(key, None)
        if source == "aws":
            aws.refresh()
        elif source == "vault":
            vault.refresh()
        val, new_source = _fetch(key)
        _CACHE[key] = val
        if new_source:
            _PROVIDER_SOURCE[key] = new_source
