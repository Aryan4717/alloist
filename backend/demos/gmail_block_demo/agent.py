#!/usr/bin/env python3
"""
Demo agent: attempts to send email via Gmail (action gmail.send).
Enforcement SDK intercepts and blocks if policy denies.
"""

import os
import sys
from pathlib import Path

# Ensure cognara_enforce is importable when run directly
_repo_root = Path(__file__).resolve().parents[3]
_enforcement_path = _repo_root / "packages" / "enforcement_py"
if _enforcement_path.exists():
    sys.path.insert(0, str(_enforcement_path))

from cognara_enforce import create_enforcement


def run_agent(token: str, to: str = "external@example.com") -> int:
    """
    Simulate agent calling gmail.send, guarded by enforcement check.
    Returns 0 if allowed, 1 if blocked.
    """
    enforcement = create_enforcement(
        api_url=os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000"),
        api_key=os.environ.get("TOKEN_SERVICE_API_KEY", ""),
        policy_service_url=os.environ.get("POLICY_SERVICE_URL", "http://localhost:8001"),
        policy_service_api_key=os.environ.get("POLICY_SERVICE_API_KEY", "dev-api-key"),
        fail_closed=True,
        high_risk_actions=["gmail.send"],
    )

    result = enforcement.check(
        token,
        action_name="gmail.send",
        metadata={"to": to},
    )

    enforcement.close()

    if not result["allowed"]:
        print(f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})")
        return 1

    print(f"Sent (evidence_id: {result['evidence_id']})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <token> [to_address]", file=sys.stderr)
        sys.exit(1)
    token = sys.argv[1]
    to = sys.argv[2] if len(sys.argv) > 2 else "external@example.com"
    sys.exit(run_agent(token, to))
