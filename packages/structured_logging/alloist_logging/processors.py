"""Structlog processors for secret redaction and exception sanitization."""

import re
from typing import Any

# Keys (case-insensitive) that should be redacted in logs
_REDACT_KEYS: set[str] = {
    "api_key",
    "apikey",
    "secret",
    "password",
    "passwd",
    "token",
    "client_secret",
    "jwt_secret",
    "private_key",
    "authorization",
    "cookie",
    "token_service_api_key",
    "policy_service_api_key",
}


def add_secret_key_for_redaction(name: str) -> None:
    """Register a key name for redaction in logs (case-insensitive)."""
    _REDACT_KEYS.add(name.lower().replace("-", "_"))


def _key_matches(key: str) -> bool:
    k = key.lower().replace("-", "_")
    return any(sk in k or k in sk for sk in _REDACT_KEYS)


def secret_redacting_processor(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor: redact secret values in event dict."""
    result = {}
    for k, v in event_dict.items():
        if _key_matches(k) and v is not None and v != "":
            result[k] = "***"
        else:
            result[k] = v
    return result


_SECRET_PATTERN = re.compile(
    r"((?:api_key|apikey|secret|password|passwd|token|client_secret|jwt_secret|private_key|authorization)"
    r"[\s=:]+)(['\"]?)([^\s'\"\n]+)\2",
    re.IGNORECASE,
)


def sanitize_exception_processor(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor: sanitize exception/traceback to remove secret values."""
    exc = event_dict.get("exception")
    if exc and isinstance(exc, str):
        event_dict["exception"] = _SECRET_PATTERN.sub(r"\1\2***\2", exc)
    return event_dict
