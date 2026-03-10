"""Revocation payload verification tests."""

import base64
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from alloist_ref_sdk import verify_revocation_payload


def sign_revocation(token_id, ts, nonce):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    payload = {"token_id": token_id, "event": "revoked", "ts": ts, "nonce": nonce}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = private_key.sign(canonical)
    from cryptography.hazmat.primitives import serialization
    pub_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        "payload": {**payload, "kid": "revocation", "signature": base64.b64encode(sig).decode("ascii")},
        "public_key_b64": base64.b64encode(pub_raw).decode("ascii"),
    }


def test_verifies_valid_payload():
    ts = datetime.now(timezone.utc).isoformat()
    out = sign_revocation("token-123", ts, str(uuid4()))
    assert verify_revocation_payload(out["payload"], public_key_b64=out["public_key_b64"]) is True


def test_rejects_stale_payload():
    old = (datetime.now(timezone.utc) - timedelta(seconds=130)).isoformat()
    out = sign_revocation("t", old, str(uuid4()))
    assert verify_revocation_payload(out["payload"], public_key_b64=out["public_key_b64"]) is False


def test_rejects_tampered_payload():
    ts = datetime.now(timezone.utc).isoformat()
    out = sign_revocation("token-123", ts, str(uuid4()))
    out["payload"]["token_id"] = "tampered"
    assert verify_revocation_payload(out["payload"], public_key_b64=out["public_key_b64"]) is False


def test_rejects_without_public_key():
    ts = datetime.now(timezone.utc).isoformat()
    out = sign_revocation("t", ts, str(uuid4()))
    assert verify_revocation_payload(out["payload"], public_key_b64=None) is False
