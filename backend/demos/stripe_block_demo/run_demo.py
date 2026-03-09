#!/usr/bin/env python3
"""
CLI orchestrator: create token, create policy (deny stripe.charge > 1000), run demo agent.
Shows blocked result with evidence_id. Optionally exports evidence bundle.
"""

import io
import os
import subprocess
import sys
from pathlib import Path

# Ensure alloist_enforce is importable
_repo_root = Path(__file__).resolve().parents[3]
_enforcement_path = _repo_root / "packages" / "enforcement_py"
if _enforcement_path.exists():
    sys.path.insert(0, str(_enforcement_path))

import httpx


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
                json={
                    "subject": subject,
                    "scopes": scopes,
                    "ttl_seconds": ttl_seconds,
                },
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
    description: str = "Deny stripe.charge when amount > 1000",
) -> bool:
    """Create policy (deny stripe.charge amount > 1000) via policy service."""
    base = api_url.rstrip("/")
    url = f"{base}/policy"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    rules = {
        "effect": "deny",
        "match": {"service": "stripe", "action_name": "charge"},
        "conditions": [
            {"field": "metadata.amount", "operator": "gt", "value": 1000}
        ],
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                url,
                json={"name": name, "description": description, "rules": rules},
                headers=headers,
            )
        if not resp.is_success:
            print(f"Policy service error: {resp.status_code} {resp.text}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Failed to create policy: {e}", file=sys.stderr)
        return False


def run_agent(token: str) -> tuple[int, str, str | None]:
    """Run demo agent. Returns (exit_code, output, evidence_id_if_blocked)."""
    from agent import run_agent as _run_agent

    evidence_id_captured: list[str] = []

    def on_blocked(result: dict) -> None:
        evidence_id_captured.append(result.get("evidence_id", ""))

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exit_code = _run_agent(token, amount=1500, on_blocked=on_blocked)
        output = sys.stdout.getvalue()
        evidence_id = evidence_id_captured[0] if evidence_id_captured else None
        return exit_code, output, evidence_id
    finally:
        sys.stdout = old_stdout


def export_and_verify_evidence(
    evidence_id: str,
    policy_url: str,
    policy_api_key: str,
    output_path: str,
) -> bool:
    """Export signed evidence via policy service API, save to file, and verify signature."""
    import json

    base = policy_url.rstrip("/")
    url = f"{base}/evidence/export"
    headers = {"Content-Type": "application/json"}
    if policy_api_key:
        headers["X-API-Key"] = policy_api_key
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json={"evidence_id": evidence_id}, headers=headers)
        if not resp.is_success:
            return False
        data = resp.json()
        bundle = data.get("bundle", {})
        Path(output_path).write_text(json.dumps(bundle, indent=2))
    except Exception:
        return False

    # Run verify_evidence.py
    policy_service_dir = Path(__file__).resolve().parents[2] / "policy_service"
    verify_script = policy_service_dir / "scripts" / "verify_evidence.py"
    try:
        result = subprocess.run(
            [sys.executable, str(verify_script), output_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("   Evidence signature verified successfully")
    except Exception:
        pass
    return True


def main() -> int:
    token_url = os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000")
    token_api_key = os.environ.get("TOKEN_SERVICE_API_KEY", "dev-api-key")
    policy_url = os.environ.get("POLICY_SERVICE_URL", "http://localhost:8001")
    policy_api_key = os.environ.get("POLICY_SERVICE_API_KEY", "dev-api-key")

    print("1. Creating token...")
    result = create_token(token_url, token_api_key)
    if not result:
        print("   Failed. Ensure token service is running (docker compose up -d).", file=sys.stderr)
        return 1
    token, token_id = result
    print(f"   Token created (id: {token_id})")

    print("2. Creating policy (deny stripe.charge amount > 1000)...")
    if not create_policy(policy_url, policy_api_key):
        return 1
    print("   Policy created")

    print("3. Running demo agent (attempts stripe.charge $1500)...")
    os.environ["TOKEN_SERVICE_URL"] = token_url
    os.environ["TOKEN_SERVICE_API_KEY"] = token_api_key
    os.environ["POLICY_SERVICE_URL"] = policy_url
    os.environ["POLICY_SERVICE_API_KEY"] = policy_api_key

    exit_code, output, evidence_id = run_agent(token)
    print(f"   {output.strip()}")

    if exit_code == 1:
        print("\nDemo complete: Agent was blocked by policy (expected).")
        print("Evidence ID shown above proves the enforcement intercept.")
        if evidence_id:
            evidence_path = "stripe_block_evidence.json"
            if export_and_verify_evidence(
                evidence_id, policy_url, policy_api_key, evidence_path
            ):
                print(f"Evidence bundle exported to {evidence_path}")
        return 0  # Blocked is expected success
    else:
        print("\nDemo complete: Agent was allowed (policy may not be active).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
