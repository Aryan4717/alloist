"""AWS Secrets Manager provider."""

import json
import os
from typing import Any

_provider_available: bool | None = None
_cached_secrets: dict[str, str] = {}
_cached_raw: str | None = None


def _is_enabled() -> bool:
    global _provider_available
    if _provider_available is not None:
        return _provider_available
    _provider_available = os.environ.get("SECRET_PROVIDER_AWS", "").lower() in (
        "1",
        "true",
        "yes",
    ) and bool(os.environ.get("AWS_SECRET_NAME"))
    return _provider_available


def _fetch_all() -> dict[str, str] | None:
    """Fetch all secrets from AWS. Returns dict or None on failure. Updates _cached_secrets."""
    global _cached_raw, _cached_secrets
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return None

    secret_name = os.environ.get("AWS_SECRET_NAME")
    if not secret_name:
        return None

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
    except (ClientError, Exception):
        return None

    secret_str = response.get("SecretString")
    if not secret_str:
        return None

    _cached_raw = secret_str
    try:
        data = json.loads(secret_str)
        if isinstance(data, dict):
            _cached_secrets = {k: str(v) for k, v in data.items() if v is not None}
            return _cached_secrets
    except json.JSONDecodeError:
        pass
    return None


def get(key: str) -> str | None:
    """Get secret from AWS Secrets Manager. Returns None if not found or error."""
    if not _is_enabled():
        return None

    # Check per-key override: SECRET_<KEY>_AWS_ID
    override_id = os.environ.get(f"SECRET_{key.upper().replace('-', '_')}_AWS_ID")
    if override_id:
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            return None
        try:
            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=override_id)
            val = response.get("SecretString")
            return val if val else None
        except (ClientError, Exception):
            return None

    # Use cached batch fetch
    if key not in _cached_secrets:
        all_secrets = _fetch_all()
        if all_secrets and key in all_secrets:
            _cached_secrets[key] = all_secrets[key]
        elif all_secrets:
            _cached_secrets[key] = None  # mark as checked
        else:
            return None

    val = _cached_secrets.get(key)
    return val if val else None


def refresh() -> None:
    """Refresh cache from AWS."""
    global _cached_secrets
    _cached_secrets.clear()
    _fetch_all()
