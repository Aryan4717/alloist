"""Verify signed revocation payloads from WebSocket."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

REVOCATION_KID = "revocation"
_MAX_AGE_SECONDS = 120
_CACHE_TTL = 300  # 5 minutes
_cached_key: tuple[bytes, float] | None = None


def _base64url_to_bytes(b64url: str) -> bytes:
    """Decode base64url to raw bytes."""
    padding = 4 - len(b64url) % 4
    if padding != 4:
        b64url += "=" * padding
    return base64.urlsafe_b64decode(b64url)


def _canonical_payload(data: dict[str, Any]) -> bytes:
    """Canonical JSON for verification (sort keys, compact)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fetch_revocation_public_key(api_url: str) -> bytes | None:
    """Fetch revocation public key from GET /keys. Caches with TTL."""
    global _cached_key
    now = time.time()
    if _cached_key and (now - _cached_key[1]) < _CACHE_TTL:
        return _cached_key[0]

    base = api_url.rstrip("/").replace("ws://", "http://").replace("wss://", "https://")
    url = f"{base}/keys"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
        if not resp.is_success:
            return _cached_key[0] if _cached_key else None
        data = resp.json()
        for key in data.get("keys", []):
            if key.get("kid") == REVOCATION_KID:
                x = key.get("x")
                if not x:
                    return None
                raw = _base64url_to_bytes(x)
                _cached_key = (raw, now)
                return raw
        return _cached_key[0] if _cached_key else None
    except Exception:
        return _cached_key[0] if _cached_key else None


def verify_revocation_payload(payload: dict[str, Any], public_key_bytes: bytes | None) -> bool:
    """
    Verify signed revocation payload.
    Returns True if signature valid and payload not expired.
    """
    if not public_key_bytes:
        return False
    signature_b64 = payload.get("signature")
    kid = payload.get("kid")
    if not signature_b64 or kid != REVOCATION_KID:
        return False

    ts_str = payload.get("ts")
    if not ts_str:
        return False
    try:
        from datetime import datetime, timezone
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age < 0 or age > _MAX_AGE_SECONDS:
            return False
    except (ValueError, TypeError):
        return False

    verify_payload = {
        "token_id": payload.get("token_id"),
        "event": payload.get("event"),
        "ts": ts_str,
        "nonce": payload.get("nonce"),
    }
    if None in verify_payload.values():
        return False

    try:
        sig = base64.b64decode(signature_b64.encode("ascii"))
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        payload_bytes = _canonical_payload(verify_payload)
        public_key.verify(sig, payload_bytes)
        return True
    except Exception:
        return False
