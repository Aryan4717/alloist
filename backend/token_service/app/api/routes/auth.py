"""OAuth (Google, GitHub) and SAML placeholder auth routes."""

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from alloist_logging import get_logger, log_event
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.jwt import encode_session_token
from app.auth.oauth import (
    build_github_auth_url,
    build_google_auth_url,
    exchange_github_code,
    exchange_google_code,
    generate_state,
)
from app.config import get_settings
from app.models import Organization, OrganizationUser, User, UserOAuthIdentity

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("token_service")

OAUTH_STATE_COOKIE = "oauth_state"


def _get_or_create_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str,
) -> User:
    """Find user by OAuth identity or email; create if new (invite-only: no org)."""
    identity = (
        db.query(UserOAuthIdentity)
        .filter(
            UserOAuthIdentity.provider == provider,
            UserOAuthIdentity.provider_user_id == provider_user_id,
        )
        .first()
    )
    if identity:
        return db.query(User).filter(User.id == identity.user_id).first()

    # New user: create User and identity
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Link existing user to this OAuth provider
        identity = UserOAuthIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
        db.add(identity)
    else:
        user = User(email=email, name=name or email.split("@")[0])
        db.add(user)
        db.flush()
        identity = UserOAuthIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
        db.add(identity)
    db.commit()
    db.refresh(user)
    return user


def _get_user_orgs(db: Session, user_id) -> list[dict]:
    """Get user's org memberships."""
    rows = (
        db.query(Organization, OrganizationUser)
        .join(OrganizationUser, OrganizationUser.org_id == Organization.id)
        .filter(OrganizationUser.user_id == user_id)
        .all()
    )
    return [
        {"id": str(org.id), "name": org.name, "role": ou.role.value}
        for org, ou in rows
    ]


@router.get("/google/login")
def google_login() -> RedirectResponse:
    """Redirect to Google OAuth."""
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )
    state = generate_state()
    url = build_google_auth_url(state)
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie(
        OAUTH_STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Exchange Google code, create/fetch user, issue JWT, redirect to frontend."""
    settings = get_settings()
    if error:
        log_event(logger, action="auth_login", result="error", provider="google", error=error)
        redirect_url = f"{settings.AUTH_CALLBACK_URL}?error={error}"
        return RedirectResponse(url=redirect_url, status_code=302)
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    # State is verified via cookie in a real impl; for now we require it
    if not state:
        raise HTTPException(status_code=400, detail="Missing state")

    try:
        user_info = await exchange_google_code(code)
    except Exception as e:
        log_event(logger, action="auth_login", result="error", provider="google", error=str(e))
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {e}")

    email = user_info.get("email") or ""
    name = user_info.get("name") or email.split("@")[0]
    provider_user_id = str(user_info.get("id", ""))

    user = _get_or_create_user(
        db, "google", provider_user_id, email, name
    )
    orgs = _get_user_orgs(db, user.id)

    org_id: UUID | None = None
    role = None
    if orgs:
        org_id = UUID(orgs[0]["id"])
        role = orgs[0]["role"]

    log_event(
        logger,
        action="auth_login",
        result="success",
        provider="google",
        user_id=str(user.id),
        org_id=str(org_id) if org_id else None,
    )

    token = encode_session_token(
        user_id=user.id,
        email=user.email,
        org_id=org_id,
        role=role,
    )
    params = {"token": token}
    if len(orgs) > 1:
        params["orgs"] = ",".join(o["id"] for o in orgs)
    redirect_url = f"{settings.AUTH_CALLBACK_URL}?{urlencode(params)}"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    return response


@router.get("/github/login")
def github_login() -> RedirectResponse:
    """Redirect to GitHub OAuth."""
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth not configured",
        )
    state = generate_state()
    url = build_github_auth_url(state)
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie(
        OAUTH_STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/github/callback")
async def github_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Exchange GitHub code, create/fetch user, issue JWT, redirect to frontend."""
    settings = get_settings()
    if error:
        msg = error_description or error
        log_event(logger, action="auth_login", result="error", provider="github", error=msg)
        redirect_url = f"{settings.AUTH_CALLBACK_URL}?error={msg}"
        return RedirectResponse(url=redirect_url, status_code=302)
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    if not state:
        raise HTTPException(status_code=400, detail="Missing state")

    try:
        user_info = await exchange_github_code(code)
    except Exception as e:
        log_event(logger, action="auth_login", result="error", provider="github", error=str(e))
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {e}")

    email = user_info.get("email", "")
    name = user_info.get("name", "") or email.split("@")[0]
    provider_user_id = str(user_info.get("id", ""))

    user = _get_or_create_user(
        db, "github", provider_user_id, email, name
    )
    orgs = _get_user_orgs(db, user.id)

    org_id: UUID | None = None
    role = None
    if orgs:
        org_id = UUID(orgs[0]["id"])
        role = orgs[0]["role"]

    log_event(
        logger,
        action="auth_login",
        result="success",
        provider="github",
        user_id=str(user.id),
        org_id=str(org_id) if org_id else None,
    )

    token = encode_session_token(
        user_id=user.id,
        email=user.email,
        org_id=org_id,
        role=role,
    )
    params = {"token": token}
    if len(orgs) > 1:
        params["orgs"] = ",".join(o["id"] for o in orgs)
    redirect_url = f"{settings.AUTH_CALLBACK_URL}?{urlencode(params)}"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    return response


@router.get("/saml/login")
def saml_login() -> Response:
    """SAML stub - not implemented."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=501,
        content={"message": "SAML SSO is not yet implemented"},
    )


@router.get("/saml/metadata")
def saml_metadata() -> Response:
    """Return SAML metadata XML for IdP configuration."""
    settings = get_settings()
    uri = settings.GOOGLE_REDIRECT_URI or "http://localhost:8000/auth/google/callback"
    base_url = uri.split("/auth/")[0] if "/auth/" in uri else "http://localhost:8000"
    entity_id = f"{base_url}/auth/saml"
    acs_url = f"{base_url}/auth/saml/acs"
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{entity_id}">
  <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="{acs_url}" index="0"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>'''
    return Response(content=xml, media_type="application/samlmetadata+xml")


@router.get("/me")
def auth_me(
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Return current user and orgs. Requires JWT or API key."""
    import hashlib
    from uuid import UUID

    from app.api.deps import _get_api_key_from_headers
    from app.auth.jwt import decode_session_token, is_jwt_like
    from app.models import ApiKey

    token = _get_api_key_from_headers(x_api_key, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization")

    user_id = None

    if is_jwt_like(token):
        payload = decode_session_token(token)
        if payload:
            user_id = UUID(payload["sub"])
    else:
        settings = get_settings()
        if settings.TOKEN_SERVICE_API_KEY and token == settings.TOKEN_SERVICE_API_KEY:
            user_id = UUID("00000000-0000-0000-0000-000000000002")
        else:
            key_hash = hashlib.sha256(token.encode()).hexdigest()
            key_prefix = token[:8] if len(token) >= 8 else token.ljust(8, "x")
            api_key_row = (
                db.query(ApiKey)
                .filter(ApiKey.key_prefix == key_prefix, ApiKey.key_hash == key_hash)
                .first()
            )
            if api_key_row:
                user_id = api_key_row.user_id

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    orgs = _get_user_orgs(db, user_id)
    return {
        "user": {"id": str(user.id), "email": user.email, "name": user.name},
        "orgs": orgs,
    }
