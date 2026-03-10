"""Token verification tests."""

import base64
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from alloist_ref_sdk import verify_token


def _to_base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def make_token(payload=None, kid="test-key-1"):
    payload = payload or {}
    jti = payload.get("jti", "test-jti")
    now = int(time.time())
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
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
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    claims = {
        "sub": payload.get("sub", "user"),
        "scopes": payload.get("scopes", ["read"]),
        "jti": jti,
        "iat": now,
        "exp": payload.get("exp", now + 3600),
        **{k: v for k, v in payload.items() if k not in ("sub", "scopes", "jti")},
    }
    token = jwt.encode(
        claims,
        private_pem,
        algorithm="EdDSA",
        headers={"kid": kid, "typ": "JWT"},
    )
    return token, jwks, jti


def test_verifies_valid_token():
    token, jwks = make_token()[:2]
    r = verify_token(token, jwks)
    assert r["valid"] is True
    assert r["jti"] == "test-jti"
    assert r["scopes"] == ["read"]
    assert r["subject"] == "user"


def test_rejects_expired_token():
    now = int(time.time())
    token, jwks = make_token({"exp": now - 60})[:2]
    r = verify_token(token, jwks)
    assert r["valid"] is False
    assert r["reason"] == "token_expired"


def test_rejects_tampered_token():
    token, jwks = make_token()[:2]
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}.{parts[2][:-2]}xx"
    r = verify_token(tampered, jwks)
    assert r["valid"] is False
    assert r["reason"] == "invalid_signature"


def test_rejects_unknown_kid():
    token, jwks = make_token({}, "key-a")[:2]
    jwks_wrong = {"keys": [{**jwks["keys"][0], "kid": "key-b"}]}
    r = verify_token(token, jwks_wrong)
    assert r["valid"] is False
