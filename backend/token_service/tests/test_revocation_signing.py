"""Unit tests for revocation signing and verification."""

from unittest.mock import patch

import pytest

from app.revocation_signing import (
    get_revocation_public_key_b64,
    sign_revocation,
    verify_revocation,
)


def test_sign_revocation_returns_expected_fields() -> None:
    """sign_revocation returns token_id, event, ts, nonce, kid, signature."""
    payload = sign_revocation("token-123")
    assert payload["token_id"] == "token-123"
    assert payload["event"] == "revoked"
    assert "ts" in payload
    assert "nonce" in payload
    assert payload["kid"] == "revocation"
    assert "signature" in payload
    assert isinstance(payload["signature"], str)


def test_verify_revocation_accepts_valid_signed_payload() -> None:
    """verify_revocation returns True for valid signed payload."""
    payload = sign_revocation("token-456")
    payload_copy = payload.copy()
    assert verify_revocation(payload_copy, get_revocation_public_key_b64()) is True


def test_verify_revocation_rejects_tampered_payload() -> None:
    """verify_revocation returns False when payload is tampered."""
    payload = sign_revocation("token-789")
    payload["token_id"] = "tampered-id"
    assert verify_revocation(payload.copy(), get_revocation_public_key_b64()) is False


def test_verify_revocation_rejects_missing_signature() -> None:
    """verify_revocation returns False when signature is missing."""
    payload = sign_revocation("token-abc")
    payload.pop("signature")
    assert verify_revocation(payload.copy(), get_revocation_public_key_b64()) is False


def test_verify_revocation_rejects_expired_payload() -> None:
    """verify_revocation returns False when ts is too old."""
    from datetime import datetime, timedelta, timezone

    payload = sign_revocation("token-xyz")
    payload["ts"] = (datetime.now(timezone.utc) - timedelta(seconds=200)).isoformat()
    assert verify_revocation(payload.copy(), get_revocation_public_key_b64()) is False
