"""Evidence signing, verification, and storage."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.evidence import Evidence


def generate_ed25519_keypair() -> tuple[str, str]:
    """Generate Ed25519 keypair. Returns (private_key_b64, public_key_b64)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_b64 = base64.b64encode(
        private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    ).decode("ascii")
    public_b64 = base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")
    return private_b64, public_b64


_ephemeral_keypair: tuple[Ed25519PrivateKey, Ed25519PublicKey] | None = None


def _get_signing_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Get evidence signing keypair from env or generate for dev (cached per process)."""
    global _ephemeral_keypair
    settings = get_settings()
    if settings.EVIDENCE_SIGNING_PRIVATE_KEY and settings.EVIDENCE_SIGNING_PUBLIC_KEY:
        raw_priv = base64.b64decode(settings.EVIDENCE_SIGNING_PRIVATE_KEY.encode("ascii"))
        raw_pub = base64.b64decode(settings.EVIDENCE_SIGNING_PUBLIC_KEY.encode("ascii"))
        return (
            Ed25519PrivateKey.from_private_bytes(raw_priv),
            Ed25519PublicKey.from_public_bytes(raw_pub),
        )
    # Dev mode: generate ephemeral keypair once per process
    if _ephemeral_keypair is None:
        priv, pub_b64 = generate_ed25519_keypair()
        raw_priv = base64.b64decode(priv.encode("ascii"))
        raw_pub = base64.b64decode(pub_b64.encode("ascii"))
        _ephemeral_keypair = (
            Ed25519PrivateKey.from_private_bytes(raw_priv),
            Ed25519PublicKey.from_public_bytes(raw_pub),
        )
    return _ephemeral_keypair


def _canonical_json(obj: dict[str, Any]) -> bytes:
    """Compact JSON with sorted keys."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_input_hash(
    action_name: str,
    token_snapshot: dict[str, Any],
    runtime_metadata: dict[str, Any] | None = None,
) -> str:
    """SHA256 of canonical JSON of input excerpt."""
    excerpt = {
        "action_name": action_name,
        "token_snapshot": token_snapshot,
        "metadata": runtime_metadata or {},
    }
    return hashlib.sha256(_canonical_json(excerpt)).hexdigest()


def _normalize_timestamp(ts: object) -> str:
    """Normalize timestamp to canonical string for signing/verification."""
    if hasattr(ts, "isoformat"):
        dt = ts
        if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt.isoformat()
    return str(ts)


def canonical_payload(evidence: dict[str, Any]) -> bytes:
    """Exclude runtime_signature, sort keys, compact JSON."""
    payload = {k: v for k, v in evidence.items() if k != "runtime_signature"}
    return _canonical_json(payload)


def sign_evidence(payload_bytes: bytes) -> str:
    """Sign payload with evidence signing key. Returns base64 signature."""
    private_key, _ = _get_signing_keypair()
    sig = private_key.sign(payload_bytes)
    return base64.b64encode(sig).decode("ascii")


def verify_evidence_signature(
    payload_bytes: bytes,
    signature_b64: str,
    public_key_b64: str | None = None,
) -> bool:
    """Verify Ed25519 signature. If public_key_b64 is None, use env key."""
    try:
        if public_key_b64:
            raw_pub = base64.b64decode(public_key_b64.encode("ascii"))
            public_key = Ed25519PublicKey.from_public_bytes(raw_pub)
        else:
            _, public_key = _get_signing_keypair()
        sig = base64.b64decode(signature_b64.encode("ascii"))
        public_key.verify(sig, payload_bytes)
        return True
    except Exception:
        return False


def get_public_key_b64() -> str:
    """Get evidence signing public key as base64."""
    _, public_key = _get_signing_keypair()
    return base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")


def create_evidence(
    db: Session,
    org_id: UUID,
    evidence_id: UUID,
    action_name: str,
    token_snapshot: dict[str, Any],
    policy_id: UUID | None,
    result: str,
    runtime_metadata: dict[str, Any] | None = None,
) -> Evidence:
    """Create, sign, and store evidence record."""
    timestamp = datetime.now(timezone.utc)
    input_hash = compute_input_hash(action_name, token_snapshot, runtime_metadata)

    # Use timestamp format that matches DB round-trip (naive isoformat for consistency)
    ts_str = _normalize_timestamp(timestamp)

    evidence_dict = {
        "evidence_id": str(evidence_id),
        "action_name": action_name,
        "token_snapshot": token_snapshot,
        "timestamp": ts_str,
        "input_hash": input_hash,
        "policy_id": str(policy_id) if policy_id else None,
        "result": result,
        "runtime_metadata": runtime_metadata or {},
    }
    payload_bytes = canonical_payload(evidence_dict)
    runtime_signature = sign_evidence(payload_bytes)

    evidence_row = Evidence(
        id=evidence_id,
        org_id=org_id,
        action_name=action_name,
        token_snapshot=token_snapshot,
        timestamp=timestamp,
        input_hash=input_hash,
        policy_id=policy_id,
        result=result,
        runtime_signature=runtime_signature,
        runtime_metadata=runtime_metadata,
    )
    db.add(evidence_row)
    db.commit()
    db.refresh(evidence_row)
    return evidence_row


def get_evidence(db: Session, org_id: UUID, evidence_id: UUID) -> Evidence | None:
    """Fetch evidence by id, scoped to org."""
    row = db.get(Evidence, evidence_id)
    return row if row and row.org_id == org_id else None


def list_evidence(
    db: Session,
    org_id: UUID,
    result: str | None = None,
    action_name: str | None = None,
    since: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Evidence], int]:
    """List evidence with optional filters. Returns (items, total)."""
    q = db.query(Evidence).filter(Evidence.org_id == org_id)
    if result:
        q = q.filter(Evidence.result == result)
    if action_name:
        q = q.filter(Evidence.action_name.ilike(f"%{action_name}%"))
    if since is not None:
        q = q.filter(Evidence.timestamp >= since)
    total = q.count()
    items = (
        q.order_by(Evidence.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def evidence_to_bundle(evidence: Evidence, public_key_b64: str) -> dict[str, Any]:
    """Convert Evidence row to signed bundle dict for export."""
    ts_str = _normalize_timestamp(evidence.timestamp)
    return {
        "evidence_id": str(evidence.id),
        "action_name": evidence.action_name,
        "token_snapshot": evidence.token_snapshot,
        "timestamp": ts_str,
        "input_hash": evidence.input_hash,
        "policy_id": str(evidence.policy_id) if evidence.policy_id else None,
        "result": evidence.result,
        "runtime_signature": evidence.runtime_signature,
        "runtime_metadata": evidence.runtime_metadata or {},
        "public_key": public_key_b64,
    }
