from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db, verify_api_key
from app.schemas.token import (
    MintTokenRequest,
    MintTokenResponse,
    RevokeTokenRequest,
    RevokeTokenResponse,
    TokenMetadataResponse,
)
from app.services.token_service import (
    TokenNotFoundError,
    NoActiveSigningKeyError,
    get_token_metadata,
    mint_token,
    revoke_token,
)
from sqlalchemy.orm import Session

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
def revoke_token_endpoint(
    body: RevokeTokenRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> RevokeTokenResponse:
    """Revoke a token by id."""
    try:
        revoke_token(db, body.token_id)
    except TokenNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return RevokeTokenResponse(success=True)


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
