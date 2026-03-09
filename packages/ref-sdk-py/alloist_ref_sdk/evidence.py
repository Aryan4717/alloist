"""Evidence bundle verification per ACT-lite spec."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canonical_json(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_evidence_bundle(bundle: dict[str, Any]) -> bool:
    """
    Verify signed evidence bundle.
    Returns True if signature valid and input_hash (when present) matches.
    """
    data = dict(bundle)
    runtime_signature = data.pop("runtime_signature", None) or data.pop("runtimeSignature", None)
    public_key_b64 = data.pop("public_key", None) or data.pop("publicKey", None)

    if not runtime_signature or not public_key_b64:
        return False

    try:
        raw_pub = base64.b64decode(public_key_b64.encode("ascii"))
        public_key = Ed25519PublicKey.from_public_bytes(raw_pub)
        sig = base64.b64decode(runtime_signature.encode("ascii"))
    except Exception:
        return False

    payload_bytes = _canonical_json(data)
    try:
        public_key.verify(sig, payload_bytes)
    except Exception:
        return False

    input_hash = data.get("input_hash")
    if input_hash:
        excerpt = {
            "action_name": data.get("action_name", ""),
            "token_snapshot": data.get("token_snapshot", {}),
            "metadata": data.get("runtime_metadata", {}),
        }
        computed = hashlib.sha256(_canonical_json(excerpt)).hexdigest()
        if computed != input_hash:
            return False

    return True
