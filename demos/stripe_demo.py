#!/usr/bin/env python3
"""
Stripe payment policy enforcement demo.
Creates token + policy (deny stripe.charge when amount > 1000), simulates $1500 charge.
"""

import os
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_enforcement_path = _repo_root / "packages" / "enforcement_py"
if _enforcement_path.exists():
    sys.path.insert(0, str(_enforcement_path))

import httpx
from alloist_enforce import create_enforcement


def create_token(
    api_url: str,
    api_key: str,
    subject: str = "demo-agent",
    scopes: list[str] | None = None,
    ttl_seconds: int = 3600,
) -> tuple[str, str] | None:
    """Create token via token service. Returns (token, token_id) or None."""
    if scopes is None:
        scopes = ["payments"]
    base = api_url.rstrip("/")
    url = f"{base}/tokens"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                url,
                json={"subject": subject, "scopes": scopes, "ttl_seconds": ttl_seconds},
                headers=headers,
            )
        if not resp.is_success:
            print(f"Token service error: {resp.status_code} {resp.text}", file=sys.stderr)
            return None
        data = resp.json()
        return data["token"], str(data["token_id"])
    except Exception as e:
        print(f"Failed to create token: {e}", file=sys.stderr)
        return None


def create_policy(
    api_url: str,
    api_key: str,
    name: str = "Block large Stripe charges",
    rules: dict = None,
) -> bool:
    """Create policy via policy service. Returns True on success."""
    if rules is None:
        rules = {
            "effect": "deny",
            "match": {"service": "stripe", "action_name": "charge"},
            "conditions": [
                {"field": "metadata.amount", "operator": "gt", "value": 1000}
            ],
        }
    base = api_url.rstrip("/")
    url = f"{base}/policy"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                url,
                json={"name": name, "rules": rules},
                headers=headers,
            )
        if not resp.is_success:
            print(f"Policy service error: {resp.status_code} {resp.text}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Failed to create policy: {e}", file=sys.stderr)
        return False


def main() -> int:
    token_url = os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000")
    token_api_key = os.environ.get("TOKEN_SERVICE_API_KEY", "dev-api-key")
    policy_url = os.environ.get("POLICY_SERVICE_URL", "http://localhost:8001")
    policy_api_key = os.environ.get("POLICY_SERVICE_API_KEY", "dev-api-key")

    result = create_token(token_url, token_api_key)
    if not result:
        print("Failed. Ensure token service is running (docker compose up -d).", file=sys.stderr)
        return 1
    token, _ = result

    if not create_policy(policy_url, policy_api_key):
        return 1

    enforcement = create_enforcement(
        api_url=token_url,
        api_key=token_api_key,
        policy_service_url=policy_url,
        policy_service_api_key=policy_api_key,
        fail_closed=True,
        high_risk_actions=["stripe.charge"],
    )

    check_result = enforcement.check(
        token,
        action_name="stripe.charge",
        metadata={"amount": 1500, "currency": "usd"},
    )
    enforcement.close()

    action = "stripe.charge"
    policy_result = "deny" if not check_result["allowed"] else "allow"
    evidence_id = check_result.get("evidence_id", "N/A")

    print("=== Alloist Demo: Stripe Payment ===\n")
    print(f"action: {action}")
    print(f"policy result: {policy_result}")
    print(f"evidence_id: {evidence_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
