from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Token, TokenStatus
from app.services.signing_service import get_active_signing_key, sign_token


class NoActiveSigningKeyError(Exception):
    """Raised when no active signing key exists for minting."""


class TokenNotFoundError(Exception):
    """Raised when a token is not found."""


def mint_token(
    db: Session,
    subject: str,
    scopes: list[str],
    ttl_seconds: int,
) -> tuple[str, UUID, datetime]:
    """Mint a new capability token. Returns (token, token_id, expires_at)."""
    key = get_active_signing_key(db)
    if not key:
        raise NoActiveSigningKeyError(
            "No active signing key. Run: python -m app.cli.rotate_key"
        )

    issued_at = datetime.now(timezone.utc)
    expires_at = datetime.fromtimestamp(
        issued_at.timestamp() + ttl_seconds,
        tz=timezone.utc,
    )

    token_row = Token(
        subject=subject,
        scopes=scopes,
        issued_at=issued_at,
        expires_at=expires_at,
        status=TokenStatus.active,
        signing_key_id=key.id,
        token_value="",  # Set after signing
    )
    db.add(token_row)
    db.flush()  # Get token_row.id

    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(token_row.id),
    }
    token_value = sign_token(db, payload, key.id)
    token_row.token_value = token_value
    db.commit()
    db.refresh(token_row)

    return token_value, token_row.id, expires_at


def revoke_token(db: Session, token_id: UUID) -> bool:
    """Revoke a token by id. Returns True if revoked."""
    token_row = db.query(Token).filter(Token.id == token_id).first()
    if not token_row:
        raise TokenNotFoundError(f"Token not found: {token_id}")

    token_row.status = TokenStatus.revoked
    db.commit()
    return True


def get_token_metadata(db: Session, token_id: UUID) -> Token | None:
    """Get token metadata by id. Returns None if not found. Excludes token_value."""
    return db.query(Token).filter(Token.id == token_id).first()
