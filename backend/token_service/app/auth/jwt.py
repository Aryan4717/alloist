"""JWT encode/decode/validate for session tokens."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import jwt

from app.config import get_settings


def encode_session_token(
    user_id: UUID,
    email: str,
    org_id: UUID | None = None,
    role: str | None = None,
) -> str:
    """Encode a session JWT."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + settings.JWT_EXPIRY_SECONDS,
    }
    if org_id is not None:
        payload["org_id"] = str(org_id)
    if role is not None:
        payload["role"] = role
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


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
