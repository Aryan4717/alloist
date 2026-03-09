from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.schemas.token import (
    MintTokenRequest,
    MintTokenResponse,
    RevokeTokenRequest,
    RevokeTokenResponse,
    TokenMetadataResponse,
    ValidateTokenRequest,
    ValidateTokenResponse,
)
from app.revocation_pubsub import publish_revocation
from app.revocation_signing import sign_revocation
from app.services.token_service import (
    NoActiveSigningKeyError,
    TokenNotFoundError,
    get_token_metadata,
    mint_token,
    revoke_token,
)
from app.ws_manager import revocation_broadcaster

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.post("", response_model=MintTokenResponse)
def create_token(
    body: MintTokenRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> MintTokenResponse:
    """Mint a new capability token."""
    try:
        token, token_id, expires_at = mint_token(
            db,
            subject=body.subject,
            scopes=body.scopes,
            ttl_seconds=body.ttl_seconds,
        )
    except NoActiveSigningKeyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    return MintTokenResponse(token=token, token_id=token_id, expires_at=expires_at)


@router.post("/revoke", response_model=RevokeTokenResponse)
async def revoke_token_endpoint(
    body: RevokeTokenRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> RevokeTokenResponse:
    """Revoke a token by id. Broadcasts to WebSocket clients."""
    try:
        revoke_token(db, body.token_id)
    except TokenNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    token_id_str = str(body.token_id)
    signed_payload = sign_revocation(token_id_str)
    published = await publish_revocation(signed_payload)
    if not published:
        await revocation_broadcaster.broadcast_revocation_payload(signed_payload)
    return RevokeTokenResponse(success=True)


@router.post("/validate", response_model=ValidateTokenResponse)
def validate_token(
    body: ValidateTokenRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> ValidateTokenResponse:
    """Validate token: verify signature, check DB status. Returns valid, status, subject, scopes, jti."""
    from app.services.signing_service import verify_token

    try:
        payload = verify_token(db, body.token)
    except jwt.InvalidTokenError:
        return ValidateTokenResponse(
            valid=False,
            status="revoked",
            subject="",
            scopes=[],
            jti="",
        )
    jti = payload.get("jti", "")
    token_row = get_token_metadata(db, UUID(jti)) if jti else None
    if not token_row:
        return ValidateTokenResponse(
            valid=False,
            status="revoked",
            subject=payload.get("sub", ""),
            scopes=payload.get("scopes", []),
            jti=jti,
        )
    return ValidateTokenResponse(
        valid=token_row.status.value == "active",
        status=token_row.status.value,
        subject=token_row.subject,
        scopes=token_row.scopes,
        jti=jti,
    )


@router.get("/{token_id}", response_model=TokenMetadataResponse)
def get_token(
    token_id: UUID,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> TokenMetadataResponse:
    """Get token metadata (no raw token value)."""
    token_row = get_token_metadata(db, token_id)
    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token not found: {token_id}",
        )
    return TokenMetadataResponse(
        id=token_row.id,
        subject=token_row.subject,
        scopes=token_row.scopes,
        issued_at=token_row.issued_at,
        expires_at=token_row.expires_at,
        status=token_row.status.value,
    )
