#!/usr/bin/env python3
"""
Export signed evidence bundle for a blocked action.
Usage: python export_evidence.py <evidence_id> [--reason "..."] [--output evidence.json]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent for evidence_schema
_schema_path = Path(__file__).resolve().parent
if str(_schema_path) not in sys.path:
    sys.path.insert(0, str(_schema_path))

from evidence_schema import EVIDENCE_BUNDLE_SCHEMA


def build_evidence_bundle(
    evidence_id: str,
    reason: str,
    action: dict | None = None,
    policy_id: str | None = None,
) -> dict:
    """Build evidence bundle dict conforming to schema placeholder."""
    if action is None:
        action = {"service": "stripe", "name": "charge", "metadata": {"amount": 1500, "currency": "usd"}}
    return {
        "evidence_id": evidence_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "result": "blocked",
        "reason": reason,
        "policy_id": policy_id,
        "signature": "placeholder",  # Placeholder for future signature
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export evidence bundle for blocked action")
    parser.add_argument("evidence_id", help="Evidence ID (UUID) from blocked result")
    parser.add_argument("--reason", default="Block large Stripe charges", help="Block reason")
    parser.add_argument(
        "--action",
        default='{"service":"stripe","name":"charge","metadata":{"amount":1500,"currency":"usd"}}',
        help="Action JSON",
    )
    parser.add_argument("--policy-id", default=None, help="Policy ID that triggered the block")
    parser.add_argument("--output", "-o", default="evidence.json", help="Output file path")
    args = parser.parse_args()

    try:
        action = json.loads(args.action)
    except json.JSONDecodeError as e:
        print(f"Invalid --action JSON: {e}", file=sys.stderr)
        return 1

    bundle = build_evidence_bundle(
        evidence_id=args.evidence_id,
        reason=args.reason,
        action=action,
        policy_id=args.policy_id,
    )

    output_path = Path(args.output)
    output_path.write_text(json.dumps(bundle, indent=2))


    print(f"Evidence bundle written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
