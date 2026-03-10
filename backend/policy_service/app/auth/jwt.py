"""JWT decode/validate for session tokens (shared secret with token_service)."""

from typing import Any

import jwt

from app.config import get_settings


def decode_session_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT. Returns payload or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def is_jwt_like(token: str) -> bool:
    """Check if string looks like a JWT (3 base64 parts)."""
    parts = token.split(".")
    return len(parts) == 3 and all(len(p) > 0 for p in parts)
