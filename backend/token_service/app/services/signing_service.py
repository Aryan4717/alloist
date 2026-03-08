import base64
import secrets
from datetime import datetime
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from sqlalchemy.orm import Session

from app.models import SigningKey


def generate_ed25519_keypair() -> tuple[str, str]:
    """Generate Ed25519 keypair. Returns (private_key_b64, public_key_b64)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_b64 = base64.b64encode(
        private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    ).decode("ascii")

    public_b64 = base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")

    return private_b64, public_b64


def _private_key_from_b64(private_b64: str) -> Ed25519PrivateKey:
    raw = base64.b64decode(private_b64.encode("ascii"))
    return Ed25519PrivateKey.from_private_bytes(raw)


def _public_key_from_b64(public_b64: str) -> Ed25519PublicKey:
    raw = base64.b64decode(public_b64.encode("ascii"))
    return Ed25519PublicKey.from_public_bytes(raw)


def get_active_signing_key(db: Session) -> SigningKey | None:
    """Get the currently active signing key."""
    return db.query(SigningKey).filter(SigningKey.is_active.is_(True)).first()


def get_signing_key_by_id(db: Session, key_id: str) -> SigningKey | None:
    """Get signing key by id (kid)."""
    return db.query(SigningKey).filter(SigningKey.id == key_id).first()


def sign_token(
    db: Session,
    payload: dict[str, Any],
    kid: str,
) -> str:
    """Sign a JWT payload with the given signing key. Returns compact JWT string."""
    key_row = get_signing_key_by_id(db, kid)
    if not key_row:
        raise ValueError(f"Signing key not found: {kid}")

    private_key = _private_key_from_b64(key_row.private_key)

    # PyJWT with Ed25519 uses the raw private key
    header = {"alg": "EdDSA", "typ": "JWT", "kid": kid}
    token = jwt.encode(
        payload,
        private_key,
        algorithm="EdDSA",
        headers=header,
    )
    return token


def verify_token(db: Session, token: str) -> dict[str, Any]:
    """Verify JWT and return payload. Raises jwt.InvalidTokenError on failure."""
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise jwt.InvalidTokenError("Missing kid in token")

    key_row = get_signing_key_by_id(db, kid)
    if not key_row:
        raise jwt.InvalidTokenError(f"Signing key not found: {kid}")

    public_key = _public_key_from_b64(key_row.public_key)
    payload = jwt.decode(token, public_key, algorithms=["EdDSA"])
    return payload


def create_signing_key_id() -> str:
    """Generate a unique signing key id."""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(8)
    return f"key_{date_part}_{random_part}"
