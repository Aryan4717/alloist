"""Enforce endpoint: Bearer capability token + action -> allow/deny."""

from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.token_ref import TokenRef, TokenStatus
from app.services.evaluator import evaluate


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EnforceRequest(BaseModel):
    action: str = Field(..., min_length=1, description="Action in dot notation, e.g. gmail.send")
    metadata: dict = Field(default_factory=dict)


class EnforceResponse(BaseModel):
    allowed: bool
    reason: str | None = None


router = APIRouter(tags=["enforce"])


def _parse_action(action: str) -> tuple[str, str]:
    """Parse 'gmail.send' -> ('gmail', 'send'). Fallback to ('unknown', action) if no dot."""
    if "." in action:
        parts = action.split(".", 1)
        return parts[0], parts[1]
    return "unknown", action


def _verify_capability_token(token: str) -> dict:
    """Verify JWT via JWKS, return payload with jti. Raises on invalid."""
    settings = get_settings()
    base = settings.TOKEN_SERVICE_URL.rstrip("/")
    jwks_url = f"{base}/keys"

    try:
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            options={"verify_exp": True},
            leeway=5,
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) if str(e) else "Invalid token",
        )


@router.post("/enforce", response_model=EnforceResponse)
def enforce(
    body: EnforceRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> EnforceResponse:
    """
    Enforce policy check using Bearer capability token.
    Returns allow/deny. On deny, returns 403.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    payload = _verify_capability_token(token)
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing jti",
        )

    try:
        token_id = UUID(jti)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token id",
        )

    token_row = db.query(TokenRef).filter(TokenRef.id == token_id).first()
    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found",
        )
    if token_row.status != TokenStatus.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
        )

    org_id = token_row.org_id
    service, name = _parse_action(body.action)

    result = evaluate(
        org_id=org_id,
        token_id=token_id,
        action={
            "service": service,
            "name": name,
            "metadata": body.metadata,
        },
        db=db,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.reason or "Action blocked by Alloist policy",
        )

    return EnforceResponse(allowed=True)
