"""Secret redaction for logs and stack traces."""

import re
from typing import Any

# Keys (case-insensitive) that should be redacted in logs
_SECRET_KEYS: set[str] = {
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
}


def register_secret_key(name: str) -> None:
    """Register a key name for redaction in logs (case-insensitive)."""
    _SECRET_KEYS.add(name.lower().replace("-", "_"))


def _key_matches(key: str) -> bool:
    k = key.lower().replace("-", "_")
    return any(sk in k or k in sk for sk in _SECRET_KEYS)


def redact_event_dict(event_dict: dict[str, Any]) -> dict[str, Any]:
    """Redact secret values in a structlog event dict. Returns new dict."""
    result = {}
    for k, v in event_dict.items():
        if _key_matches(k) and v is not None and v != "":
            result[k] = "***"
        else:
            result[k] = v
    return result


# Pattern to redact secret=value or key: value in exception strings
_SECRET_PATTERN = re.compile(
    r"((?:api_key|apikey|secret|password|passwd|token|client_secret|jwt_secret|private_key|authorization)"
    r"[\s=:]+)(['\"]?)([^\s'\"\n]+)\2",
    re.IGNORECASE,
)


def sanitize_exception_text(text: str) -> str:
    """Replace secret values in exception/traceback text with ***."""
    if not text or not isinstance(text, str):
        return text
    return _SECRET_PATTERN.sub(r"\1\2***\2", text)
