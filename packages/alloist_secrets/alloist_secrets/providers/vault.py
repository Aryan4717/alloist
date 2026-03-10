"""Hashicorp Vault provider."""

import os
from typing import Any

_provider_available: bool | None = None
_client: Any = None


def _is_enabled() -> bool:
    global _provider_available
    if _provider_available is not None:
        return _provider_available
    _provider_available = os.environ.get("SECRET_PROVIDER_VAULT", "").lower() in (
        "1",
        "true",
        "yes",
    ) and bool(os.environ.get("VAULT_ADDR")) and bool(os.environ.get("VAULT_TOKEN"))
    return _provider_available


def _get_client() -> Any:
    global _client
    if _client is not None:
        return _client
    try:
        import hvac
    except ImportError:
        return None
    addr = os.environ.get("VAULT_ADDR")
    token = os.environ.get("VAULT_TOKEN")
    if not addr or not token:
        return None
    try:
        _client = hvac.Client(url=addr, token=token)
        if not _client.is_authenticated():
            _client = None
            return None
        return _client
    except Exception:
        return None


def get(key: str) -> str | None:
    """Get secret from Vault. Returns None if not found or error."""
    if not _is_enabled():
        return None

    # Per-key path: SECRET_<KEY>_VAULT_PATH or default path
    path_env = f"SECRET_{key.upper().replace('-', '_')}_VAULT_PATH"
    default_path = os.environ.get("VAULT_SECRET_PATH", "alloist")
    path = os.environ.get(path_env) or default_path
    # Strip secret/ or secret/data/ prefix for hvac path param
    mount = "secret"
    if path.startswith("secret/"):
        path = path[7:]
    if path.startswith("data/"):
        path = path[5:]
    path_parts = path.split("/")
    kv_path = path_parts[-1] if path_parts else "alloist"

    client = _get_client()
    if not client:
        return None

    try:
        # hvac kv v2: read_secret_version(path=key)
        read_response = client.secrets.kv.v2.read_secret_version(path=kv_path)
        data = read_response.get("data", {}).get("data", {})
        val = data.get(key)
        return str(val) if val is not None else None
    except Exception:
        try:
            read_response = client.secrets.kv.v1.read_secret(path=kv_path)
            val = read_response.get("data", {}).get(key)
            return str(val) if val is not None else None
        except Exception:
            return None


def refresh() -> None:
    """Refresh - clear client to force re-auth on next get."""
    global _client
    _client = None
