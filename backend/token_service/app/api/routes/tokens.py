from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status

from alloist_logging import get_logger, log_event
from alloist_metrics import create_metrics
from sqlalchemy.orm import Session

from app.api.deps import OrgContext, get_db, require_role, require_usage_available
from app.models import OrgRole
from app.revocation_pubsub import publish_revocation
from app.revocation_signing import sign_revocation
from app.schemas.token import (
    MintTokenRequest,
    MintTokenResponse,
    RevokeTokenRequest,
    RevokeTokenResponse,
    TokenListResponse,
    TokenMetadataResponse,
    ValidateTokenRequest,
    ValidateTokenResponse,
)
from app.services.token_service import (
    NoActiveSigningKeyError,
    TokenNotFoundError,
    get_token_metadata,
    list_tokens,
    mint_token,
    revoke_token,
)
from app.ws_manager import revocation_broadcaster

router = APIRouter(prefix="/tokens", tags=["tokens"])
logger = get_logger("token_service")
metrics = create_metrics("token_service")

ROLE_READ = require_role(OrgRole.admin, OrgRole.developer, OrgRole.viewer)
ROLE_WRITE = require_role(OrgRole.admin, OrgRole.developer)
ROLE_ADMIN = require_role(OrgRole.admin)


@router.get("", response_model=TokenListResponse)
def list_tokens_endpoint(
    status: str | None = None,
    subject: str | None = None,
    limit: int = 50,
    offset: int = 0,
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> TokenListResponse:
    """List tokens with optional filters."""
    items, total = list_tokens(
        db,
        org_id=ctx.org_id,
        status=status,
        subject=subject,
        limit=limit,
        offset=offset,
    )
    return TokenListResponse(
        items=[
            TokenMetadataResponse(
                id=t.id,
                subject=t.subject,
                scopes=t.scopes,
                issued_at=t.issued_at,
                expires_at=t.expires_at,
                status=t.status.value,
            )
            for t in items
        ],
        total=total,
    )


@router.post("", response_model=MintTokenResponse)
def create_token(
    body: MintTokenRequest,
    ctx: OrgContext = ROLE_WRITE,
    db: Session = Depends(get_db),
    _: OrgContext = require_usage_available("tokens_created"),
) -> MintTokenResponse:
    """Mint a new capability token."""
    try:
        token, token_id, expires_at = mint_token(
            db,
            org_id=ctx.org_id,
            subject=body.subject,
            scopes=body.scopes,
            ttl_seconds=body.ttl_seconds,
        )
    except NoActiveSigningKeyError as e:
        log_event(
            logger,
            action="token_created",
            result="error",
            org_id=ctx.org_id,
            user_id=ctx.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    log_event(
        logger,
        action="token_created",
        result="success",
        org_id=ctx.org_id,
        user_id=ctx.user_id,
        token_id=str(token_id),
        subject=body.subject,
    )
    from app.services.billing_service import increment_usage

    increment_usage(db, ctx.org_id, "tokens_created")
    metrics.inc_token_issuance()
    return MintTokenResponse(token=token, token_id=token_id, expires_at=expires_at)


@router.post("/revoke", response_model=RevokeTokenResponse)
async def revoke_token_endpoint(
    body: RevokeTokenRequest,
    ctx: OrgContext = ROLE_ADMIN,
    db: Session = Depends(get_db),
) -> RevokeTokenResponse:
    """Revoke a token by id. Broadcasts to WebSocket clients. Admin only."""
    try:
        revoke_token(db, ctx.org_id, body.token_id)
    except TokenNotFoundError as e:
        log_event(
            logger,
            action="token_revoked",
            result="error",
            org_id=ctx.org_id,
            user_id=ctx.user_id,
            token_id=str(body.token_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    log_event(
        logger,
        action="token_revoked",
        result="success",
        org_id=ctx.org_id,
        user_id=ctx.user_id,
        token_id=str(body.token_id),
    )
    metrics.inc_revocation_events()
    token_id_str = str(body.token_id)
    signed_payload = sign_revocation(token_id_str)
    published = await publish_revocation(signed_payload)
    if not published:
        await revocation_broadcaster.broadcast_revocation_payload(signed_payload)
    return RevokeTokenResponse(success=True)


@router.post("/validate", response_model=ValidateTokenResponse)
def validate_token(
    body: ValidateTokenRequest,
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> ValidateTokenResponse:
    """Validate token: verify signature, check DB status."""
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
    token_row = get_token_metadata(db, ctx.org_id, UUID(jti)) if jti else None
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
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> TokenMetadataResponse:
    """Get token metadata (no raw token value)."""
    token_row = get_token_metadata(db, ctx.org_id, token_id)
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
