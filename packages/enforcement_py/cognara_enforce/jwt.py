"""Local JWT verification with JWKS (Ed25519)."""

from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWKClient, PyJWKSet
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


def verify_token_locally(
    token: str,
    api_url: str,
    jwks_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Verify JWT signature and TTL locally.
    Returns {valid: True, jti, scopes, subject} or {valid: False, reason}.
    """
    base = api_url.rstrip("/")
    jwks_url = f"{base}/keys"

    try:
        if jwks_override:
            jwk_set = PyJWKSet.from_dict(jwks_override)
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            signing_key = None
            for key in jwk_set.keys:
                if key.key_id == kid:
                    signing_key = key
                    break
            if not signing_key:
                return {"valid": False, "reason": "key_not_found"}
        else:
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            options={"verify_exp": True},
            leeway=5,
        )

        jti = payload.get("jti", "")
        scopes = payload.get("scopes", [])
        subject = payload.get("sub", "")
        return {"valid": True, "jti": jti, "scopes": scopes, "subject": subject}

    except ExpiredSignatureError:
        return {"valid": False, "reason": "token_expired"}
    except jwt.InvalidSignatureError:
        return {"valid": False, "reason": "invalid_signature"}
    except InvalidTokenError as e:
        return {"valid": False, "reason": str(e) if str(e) else "invalid_token"}
