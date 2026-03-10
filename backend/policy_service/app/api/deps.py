import hashlib
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import ApiKey, OrgRole, OrganizationUser

DEFAULT_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass
class OrgContext:
    user_id: UUID
    org_id: UUID
    role: OrgRole


def _get_api_key_from_headers(
    x_api_key: str | None = None,
    authorization: str | None = None,
) -> str | None:
    if x_api_key:
        return x_api_key
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def get_org_id(
    x_org_id: Annotated[str | None, Header(alias="X-Org-Id")] = None,
) -> UUID:
    """Extract org_id from X-Org-Id header. Returns default org if missing (backward compat)."""
    if x_org_id:
        try:
            return UUID(x_org_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Org-Id format",
            )
    return DEFAULT_ORG_ID


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    org_id: Annotated[UUID, Depends(get_org_id)],
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> OrgContext:
    """
    Resolve JWT or API key to user and role in org.
    JWT takes precedence if Bearer token looks like a JWT.
    Legacy POLICY_SERVICE_API_KEY maps to default org + admin.
    """
    from app.auth.jwt import decode_session_token, is_jwt_like

    token = _get_api_key_from_headers(x_api_key, authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    if is_jwt_like(token):
        payload = decode_session_token(token)
        if payload:
            user_id = UUID(payload["sub"])
            jwt_org_id = payload.get("org_id")
            jwt_role = payload.get("role")
            if jwt_org_id is None or jwt_role is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No organization access",
                )
            if str(jwt_org_id) != str(org_id):
                ou = (
                    db.query(OrganizationUser)
                    .filter(
                        OrganizationUser.user_id == user_id,
                        OrganizationUser.org_id == org_id,
                    )
                    .first()
                )
                if not ou:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User not in organization",
                    )
                return OrgContext(user_id=user_id, org_id=org_id, role=ou.role)
            return OrgContext(
                user_id=user_id,
                org_id=UUID(jwt_org_id),
                role=OrgRole(jwt_role),
            )

    settings = get_settings()
    if settings.POLICY_SERVICE_API_KEY and token == settings.POLICY_SERVICE_API_KEY:
        return OrgContext(
            user_id=DEFAULT_USER_ID,
            org_id=org_id,
            role=OrgRole.admin,
        )

    key_hash = hashlib.sha256(token.encode()).hexdigest()
    key_prefix = token[:8] if len(token) >= 8 else token.ljust(8, "x")
    api_key_row = (
        db.query(ApiKey)
        .filter(ApiKey.key_prefix == key_prefix, ApiKey.key_hash == key_hash)
        .first()
    )
    if not api_key_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    ou = (
        db.query(OrganizationUser)
        .filter(
            OrganizationUser.user_id == api_key_row.user_id,
            OrganizationUser.org_id == org_id,
        )
        .first()
    )
    if not ou:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not in organization",
        )

    return OrgContext(user_id=api_key_row.user_id, org_id=org_id, role=ou.role)


def require_usage_available(metric: str):
    """Dependency that blocks request if org usage limit exceeded."""

    def _check(
        ctx: Annotated[OrgContext, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> OrgContext:
        from app.services.billing_service import check_usage_limit

        if not check_usage_limit(db, ctx.org_id, metric):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Usage limit exceeded for {metric}. Upgrade your plan.",
            )
        return ctx

    return Depends(_check)


def require_policy_evaluation_usage(*roles: OrgRole):
    """Dependency for /policy/evaluate: checks role and enforcement_checks or policy_evaluations based on X-Request-Type."""

    def _check(
        ctx: Annotated[OrgContext, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        x_request_type: Annotated[str | None, Header(alias="X-Request-Type")] = None,
    ) -> OrgContext:
        if roles and ctx.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {[r.value for r in roles]}",
            )
        from app.services.billing_service import check_usage_limit

        metric = "enforcement_checks" if x_request_type == "enforcement" else "policy_evaluations"
        if not check_usage_limit(db, ctx.org_id, metric):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Usage limit exceeded for {metric}. Upgrade your plan.",
            )
        return ctx

    return Depends(_check)


def require_role(*roles: OrgRole):
    """Dependency that requires current user to have one of the given roles."""

    def _check(ctx: Annotated[OrgContext, Depends(get_current_user)]) -> OrgContext:
        if ctx.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {[r.value for r in roles]}",
            )
        return ctx

    return Depends(_check)


def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Verify API key. Legacy auth for routes that don't need RBAC."""
    api_key = get_settings().POLICY_SERVICE_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured",
        )

    provided = _get_api_key_from_headers(x_api_key, authorization)
    if not provided or provided != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
