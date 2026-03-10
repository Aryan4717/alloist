#!/usr/bin/env python3
"""
Token revocation demo.
Creates token, allows first action, revokes token, blocks second action.
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
        scopes = ["read"]
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


def revoke_token(api_url: str, api_key: str, token_id: str) -> bool:
    """Revoke token via token service."""
    base = api_url.rstrip("/")
    url = f"{base}/tokens/revoke"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json={"token_id": token_id}, headers=headers)
        return resp.is_success
    except Exception:
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
    token, token_id = result

    enforcement = create_enforcement(
        api_url=token_url,
        api_key=token_api_key,
        policy_service_url=policy_url,
        policy_service_api_key=policy_api_key,
        fail_closed=True,
        high_risk_actions=["test.read"],
    )

    print("=== Alloist Demo: Token Revocation ===\n")

    # Use neutral action so no deny policy blocks (policies may persist from other demos)
    action = "test.read"
    check1 = enforcement.check(
        token,
        action_name=action,
        metadata={},
    )
    policy_result1 = "allow" if check1["allowed"] else "deny"
    evidence_id1 = check1.get("evidence_id", "N/A")
    print(f"action: {action}")
    print(f"policy result: {policy_result1}")
    print(f"evidence_id: {evidence_id1}")
    print()

    print("[Revoking token...]")
    if not revoke_token(token_url, token_api_key, token_id):
        print("Failed to revoke token.", file=sys.stderr)
        enforcement.close()
        return 1
    print()

    check2 = enforcement.check(
        token,
        action_name=action,
        metadata={},
    )
    policy_result2 = "deny" if not check2["allowed"] else "allow"
    reason2 = check2.get("reason") or ""
    if not check2["allowed"] and ("revoked" in reason2 or "token_revoked" in reason2):
        policy_result2 = "deny (token_revoked)"
    evidence_id2 = check2.get("evidence_id", "N/A")
    print(f"action: {action}")
    print(f"policy result: {policy_result2}")
    print(f"evidence_id: {evidence_id2}")

    enforcement.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
