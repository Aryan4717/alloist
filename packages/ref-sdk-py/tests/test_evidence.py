"""Evidence bundle verification tests."""

import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from alloist_ref_sdk import verify_evidence_bundle


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_bundle(bundle):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    data = {k: v for k, v in bundle.items() if k not in ("runtime_signature", "public_key")}
    payload = _canonical(data)
    sig = private_key.sign(payload)
    from cryptography.hazmat.primitives import serialization
    pub_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {
        **data,
        "runtime_signature": base64.b64encode(sig).decode("ascii"),
        "public_key": base64.b64encode(pub_raw).decode("ascii"),
    }


def test_verifies_valid_bundle():
    bundle = {
        "evidence_id": "e1",
        "action_name": "gmail.send",
        "token_snapshot": {"jti": "t1"},
        "timestamp": "2026-01-09T12:00:00",
        "result": "deny",
        "runtime_metadata": {},
    }
    signed = sign_bundle(bundle)
    assert verify_evidence_bundle(signed) is True


def test_rejects_tampered_bundle():
    bundle = {
        "evidence_id": "e1",
        "action_name": "gmail.send",
        "token_snapshot": {},
        "timestamp": "2026-01-09T12:00:00",
        "result": "deny",
        "runtime_metadata": {},
    }
    signed = sign_bundle(bundle)
    signed["action_name"] = "tampered"
    assert verify_evidence_bundle(signed) is False


def test_verifies_input_hash():
    excerpt = {"action_name": "a", "token_snapshot": {}, "metadata": {}}
    input_hash = hashlib.sha256(_canonical(excerpt)).hexdigest()
    bundle = {
        "evidence_id": "e1",
        "action_name": "a",
        "token_snapshot": {},
        "timestamp": "2026-01-09T12:00:00",
        "input_hash": input_hash,
        "result": "deny",
        "runtime_metadata": {},
    }
    signed = sign_bundle(bundle)
    assert verify_evidence_bundle(signed) is True


def test_rejects_missing_signature():
    assert verify_evidence_bundle({"evidence_id": "e1", "public_key": "dGVzdA=="}) is False
