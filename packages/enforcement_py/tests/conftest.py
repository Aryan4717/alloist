"""Pytest fixtures for alloist_enforce tests."""

import base64
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def _to_base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def make_test_token(
    payload: dict | None = None,
    kid: str = "test-key-1",
) -> tuple[str, dict, str]:
    """
    Generate Ed25519-signed JWT and JWKS for verification.
    Returns (token, jwks, jti).
    """
    payload = payload or {}
    jti = payload.get("jti", "test-jti-123")
    now = int(time.time())

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # JWK for public key (Ed25519)
    pub_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    jwk = {
        "kty": "OKP",
        "crv": "Ed25519",
        "kid": kid,
        "alg": "EdDSA",
        "x": _to_base64url(pub_raw),
    }
    jwks = {"keys": [jwk]}

    # Sign JWT - PyJWT needs PEM or raw for Ed25519
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PrivateFormat,
        PublicFormat,
    )

    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    claims = {
        "sub": payload.get("sub", "test-user"),
        "scopes": payload.get("scopes", ["email:send"]),
        "jti": jti,
        "iat": now,
        "exp": now + 3600,
        **{k: v for k, v in payload.items() if k not in ("sub", "scopes", "jti")},
    }

    token = jwt.encode(
        claims,
        private_pem,
        algorithm="EdDSA",
        headers={"kid": kid, "typ": "JWT"},
    )
    return token, jwks, jti
