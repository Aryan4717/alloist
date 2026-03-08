"""JWKS endpoint - public keys for JWT verification."""
import base64

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import SigningKey

router = APIRouter(prefix="/keys", tags=["keys"])


def _to_base64url(b64_standard: str) -> str:
    """Convert standard base64 to base64url (no padding)."""
    raw = base64.b64decode(b64_standard.encode("ascii"))
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@router.get("")
def get_jwks(db: Session = Depends(get_db)) -> dict:
    """Return JSON Web Key Set with all signing keys (public only). No auth required."""
    keys = db.query(SigningKey).all()
    jwks = {
        "keys": [
            {
                "kty": "OKP",
                "crv": "Ed25519",
                "kid": k.id,
                "x": _to_base64url(k.public_key),
            }
            for k in keys
        ]
    }
    return jwks
