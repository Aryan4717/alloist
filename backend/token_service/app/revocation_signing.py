"""Sign and verify revocation events (Ed25519)."""

from __future__ import annotations

import base64
import json
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.config import get_settings

REVOCATION_KID = "revocation"
_MAX_AGE_SECONDS = 120  # Reject payloads older than 2 minutes

_ephemeral_keypair: tuple[Ed25519PrivateKey, Ed25519PublicKey] | None = None


def _get_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Get revocation signing keypair from env or generate ephemeral (cached)."""
    global _ephemeral_keypair
    settings = get_settings()
    priv_b64 = settings.REVOCATION_SIGNING_PRIVATE_KEY or ""
    pub_b64 = settings.REVOCATION_SIGNING_PUBLIC_KEY or ""

    if priv_b64 and pub_b64:
        raw_priv = base64.b64decode(priv_b64.encode("ascii"))
        raw_pub = base64.b64decode(pub_b64.encode("ascii"))
        return (
            Ed25519PrivateKey.from_private_bytes(raw_priv),
            Ed25519PublicKey.from_public_bytes(raw_pub),
        )

    if _ephemeral_keypair is None:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        _ephemeral_keypair = (private_key, public_key)
    return _ephemeral_keypair


def _canonical_payload(data: dict[str, Any]) -> bytes:
    """Canonical JSON for signing (sort keys, compact)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_revocation(token_id: str) -> dict[str, Any]:
    """
    Build and sign a revocation payload.
    Returns dict with token_id, event, ts, nonce, kid, signature.
    """
    ts = datetime.now(timezone.utc).isoformat()
    nonce = str(uuid4())
    payload = {
        "token_id": token_id,
        "event": "revoked",
        "ts": ts,
        "nonce": nonce,
    }
    payload_bytes = _canonical_payload(payload)
    private_key, _ = _get_keypair()
    sig = private_key.sign(payload_bytes)
    sig_b64 = base64.b64encode(sig).decode("ascii")

    return {
        **payload,
        "kid": REVOCATION_KID,
        "signature": sig_b64,
    }


def get_revocation_public_key_b64() -> str:
    """Get revocation public key as base64 (for SDK verification)."""
    _, public_key = _get_keypair()
    return base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")


def verify_revocation(payload: dict[str, Any], public_key_b64: str | None = None) -> bool:
    """
    Verify signed revocation payload.
    Returns True if signature valid and payload not expired.
    """
    signature_b64 = payload.pop("signature", None)
    kid = payload.pop("kid", None)
    if not signature_b64 or not kid:
        return False

    ts_str = payload.get("ts")
    if not ts_str:
        return False
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age < 0 or age > _MAX_AGE_SECONDS:
            return False
    except (ValueError, TypeError):
        return False

    key_b64 = public_key_b64 or get_revocation_public_key_b64()
    try:
        raw_pub = base64.b64decode(key_b64.encode("ascii"))
        public_key = Ed25519PublicKey.from_public_bytes(raw_pub)
        sig = base64.b64decode(signature_b64.encode("ascii"))
    except Exception:
        return False

    payload_bytes = _canonical_payload(payload)
    try:
        public_key.verify(sig, payload_bytes)
        return True
    except Exception:
        return False
