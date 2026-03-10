#!/usr/bin/env python3
"""
Demo agent: attempts Stripe charge (action stripe.charge).
Enforcement SDK intercepts and blocks if policy denies (e.g., amount > 1000).
"""

import os
import sys
from pathlib import Path
from typing import Callable

# Ensure alloist_enforce is importable when run directly
_repo_root = Path(__file__).resolve().parents[3]
_enforcement_path = _repo_root / "packages" / "enforcement_py"
if _enforcement_path.exists():
    sys.path.insert(0, str(_enforcement_path))

from alloist_enforce import create_enforcement


def run_agent(
    token: str,
    amount: int = 1500,
    currency: str = "usd",
    on_blocked: Callable | None = None,
) -> int:
    """
    Simulate agent calling stripe.charge, guarded by enforcement check.
    Returns 0 if allowed, 1 if blocked.
    on_blocked: optional callback(result) when blocked, for evidence export.
    """
    enforcement = create_enforcement(
        api_url=os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000"),
        api_key=os.environ.get("TOKEN_SERVICE_API_KEY", ""),
        policy_service_url=os.environ.get("POLICY_SERVICE_URL", "http://localhost:8001"),
        policy_service_api_key=os.environ.get("POLICY_SERVICE_API_KEY", "dev-api-key"),
        fail_closed=True,
        high_risk_actions=["stripe.charge"],
    )

    metadata = {"amount": amount, "currency": currency}
    result = enforcement.check(
        token,
        action_name="stripe.charge",
        metadata=metadata,
    )

    enforcement.close()

    if not result["allowed"]:
        print(f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})")
        if on_blocked:
            on_blocked(result)
        return 1

    print(f"Charged (evidence_id: {result['evidence_id']})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <token> [amount] [currency]", file=sys.stderr)
        sys.exit(1)
    token = sys.argv[1]
    amount = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    currency = sys.argv[3] if len(sys.argv) > 3 else "usd"
    sys.exit(run_agent(token, amount=amount, currency=currency))
