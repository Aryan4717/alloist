"""JWKS endpoint - public keys for JWT verification and revocation."""
import base64

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import SigningKey
from app.revocation_signing import get_revocation_public_key_b64

router = APIRouter(prefix="/keys", tags=["keys"])


def _to_base64url(b64_standard: str) -> str:
    """Convert standard base64 to base64url (no padding)."""
    raw = base64.b64decode(b64_standard.encode("ascii"))
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@router.get("")
def get_jwks(db: Session = Depends(get_db)) -> dict:
    """Return JSON Web Key Set with all signing keys (public only). No auth required."""
    keys = db.query(SigningKey).all()
    jwks_keys = [
        {
            "kty": "OKP",
            "crv": "Ed25519",
            "kid": k.id,
            "x": _to_base64url(k.public_key),
        }
        for k in keys
    ]
    # Add revocation key for SDK verification of revocation events
    rev_pub = get_revocation_public_key_b64()
    jwks_keys.append({
        "kty": "OKP",
        "crv": "Ed25519",
        "kid": "revocation",
        "use": "revocation",
        "x": _to_base64url(rev_pub),
    })
    return {"keys": jwks_keys}
