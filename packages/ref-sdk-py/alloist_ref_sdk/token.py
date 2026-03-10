"""Token verification with JWKS (Ed25519)."""

from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWKSet
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


def verify_token(token: str, jwks: dict[str, Any]) -> dict[str, Any]:
    """
    Verify ACT-lite JWT with JWKS.
    Returns {valid: True, jti, scopes, subject} or {valid: False, reason}.
    """
    try:
        jwk_set = PyJWKSet.from_dict(jwks)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        signing_key = None
        for key in jwk_set.keys:
            if key.key_id == kid:
                signing_key = key
                break
        if not signing_key:
            return {"valid": False, "reason": "key_not_found"}

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            options={"verify_exp": True},
            leeway=5,
        )
        return {
            "valid": True,
            "jti": payload.get("jti", ""),
            "scopes": payload.get("scopes", []),
            "subject": payload.get("sub", ""),
        }
    except ExpiredSignatureError:
        return {"valid": False, "reason": "token_expired"}
    except jwt.InvalidSignatureError:
        return {"valid": False, "reason": "invalid_signature"}
    except InvalidTokenError as e:
        return {"valid": False, "reason": str(e) if str(e) else "invalid_token"}
