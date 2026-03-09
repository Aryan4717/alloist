#!/usr/bin/env python3
"""
Verify signed evidence bundle.
Usage: python verify_evidence.py <evidence_bundle.json> [--public-key base64]
Exit 0 if valid, 1 if invalid or tampered.
"""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

# Add app to path
_script_dir = Path(__file__).resolve().parent
_app_dir = _script_dir.parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_bundle(bundle_path: Path, public_key_b64: str | None = None) -> bool:
    """Verify evidence bundle signature and input_hash. Returns True if valid."""
    data = json.loads(bundle_path.read_text())

    # Extract fields
    runtime_signature = data.pop("runtime_signature", None)
    public_key_from_bundle = data.pop("public_key", None)

    if not runtime_signature:
        print("Missing runtime_signature", file=sys.stderr)
        return False

    # Use provided key, or key from bundle
    key_b64 = public_key_b64 or public_key_from_bundle
    if not key_b64:
        print("No public key (use --public-key or ensure bundle has public_key)", file=sys.stderr)
        return False

    try:
        raw_pub = base64.b64decode(key_b64.encode("ascii"))
        public_key = Ed25519PublicKey.from_public_bytes(raw_pub)
        sig = base64.b64decode(runtime_signature.encode("ascii"))
    except Exception as e:
        print(f"Invalid key or signature: {e}", file=sys.stderr)
        return False

    # Recompute canonical payload (what was signed)
    payload_bytes = _canonical_json(data)

    try:
        public_key.verify(sig, payload_bytes)
    except Exception:
        print("Signature verification failed (tampered or invalid)", file=sys.stderr)
        return False

    # Verify input_hash if present
    input_hash = data.get("input_hash")
    if input_hash:
        action_name = data.get("action_name", "")
        token_snapshot = data.get("token_snapshot", {})
        runtime_metadata = data.get("runtime_metadata", {})
        excerpt = {
            "action_name": action_name,
            "token_snapshot": token_snapshot,
            "metadata": runtime_metadata,
        }
        computed = hashlib.sha256(_canonical_json(excerpt)).hexdigest()
        if computed != input_hash:
            print("input_hash mismatch (content tampered)", file=sys.stderr)
            return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify signed evidence bundle")
    parser.add_argument("bundle", type=Path, help="Path to evidence bundle JSON")
    parser.add_argument("--public-key", help="Base64 public key (optional if bundle has public_key)")
    args = parser.parse_args()

    if not args.bundle.exists():
        print(f"File not found: {args.bundle}", file=sys.stderr)
        return 1

    if verify_bundle(args.bundle, args.public_key):
        print("Evidence bundle valid")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
