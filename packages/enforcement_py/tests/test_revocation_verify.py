"""Tests for revocation payload verification."""

import base64
import json
from datetime import datetime, timezone
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cognara_enforce.revocation_verify import (
    fetch_revocation_public_key,
    verify_revocation_payload,
)


def test_verify_revocation_payload_accepts_valid_signed() -> None:
    """verify_revocation_payload returns True for valid Ed25519-signed payload."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    payload = {
        "token_id": "t1",
        "event": "revoked",
        "ts": datetime.now(timezone.utc).isoformat(),
        "nonce": "abc-123",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = private_key.sign(canonical)
    payload["signature"] = base64.b64encode(sig).decode("ascii")
    payload["kid"] = "revocation"

    assert verify_revocation_payload(payload, pub_bytes) is True


def test_verify_revocation_payload_rejects_tampered() -> None:
    """verify_revocation_payload returns False when payload is tampered."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    payload = {
        "token_id": "t1",
        "event": "revoked",
        "ts": datetime.now(timezone.utc).isoformat(),
        "nonce": "abc-123",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = private_key.sign(canonical)
    payload["signature"] = base64.b64encode(sig).decode("ascii")
    payload["kid"] = "revocation"
    payload["token_id"] = "tampered"

    assert verify_revocation_payload(payload, pub_bytes) is False


def test_verify_revocation_payload_rejects_no_public_key() -> None:
    """verify_revocation_payload returns False when public_key is None."""
    payload = {
        "token_id": "t1",
        "event": "revoked",
        "ts": "2024-01-01T00:00:00+00:00",
        "nonce": "x",
        "signature": "YQ==",
        "kid": "revocation",
    }
    assert verify_revocation_payload(payload, None) is False


def test_fetch_revocation_public_key_returns_key_from_jwks() -> None:
    """fetch_revocation_public_key fetches and parses revocation key from GET /keys."""
    import cognara_enforce.revocation_verify as rv

    rv._cached_key = None  # Clear cache for fresh fetch
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    x_b64url = base64.urlsafe_b64encode(pub_raw).decode("ascii").rstrip("=")

    jwks_response = {
        "keys": [
            {"kty": "OKP", "crv": "Ed25519", "kid": "revocation", "x": x_b64url},
        ],
    }

    class MockResponse:
        ok = True
        is_success = True

        def json(self):
            return jwks_response

    with patch("cognara_enforce.revocation_verify.httpx.Client") as mock_client:
        ctx = mock_client.return_value.__enter__.return_value
        ctx.get.return_value = MockResponse()
        result = fetch_revocation_public_key("http://localhost:8000")

    assert result is not None
    assert len(result) == 32
