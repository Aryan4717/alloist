#!/usr/bin/env python3
"""
YC Demo: Full flow for recording.
1. Create token + policy to block Gmail send
2. Run agent attempt -> blocked (show evidence_id)
3. Revoke token mid-flow
4. Run agent again -> blocked (token_revoked)
5. Export evidence package -> verify signature
"""

import io
import json
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
        scopes = ["email:send"]
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
    name: str = "Block Gmail send",
    description: str = "Deny gmail.send for demo",
) -> bool:
    """Create policy (deny gmail.send) via policy service."""
    base = api_url.rstrip("/")
    url = f"{base}/policy"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    rules = {
        "effect": "deny",
        "match": {"service": "gmail", "action_name": "send"},
        "conditions": [],
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


def run_agent(token: str) -> tuple[int, str, str | None]:
    """Run demo agent. Returns (exit_code, output, evidence_id_if_blocked)."""
    gmail_demo = Path(__file__).resolve().parent.parent / "gmail_block_demo"
    if str(gmail_demo) not in sys.path:
        sys.path.insert(0, str(gmail_demo))
    from agent import run_agent as _run_agent

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exit_code = _run_agent(token)
        output = sys.stdout.getvalue()
        # Parse evidence_id from "Blocked: ... (evidence_id: <uuid>)"
        evidence_id = None
        if "(evidence_id:" in output:
            start = output.find("(evidence_id:") + len("(evidence_id:")
            end = output.find(")", start)
            if end > start:
                evidence_id = output[start:end].strip()
        return exit_code, output, evidence_id
    finally:
        sys.stdout = old_stdout


def export_and_verify_evidence(
    evidence_id: str,
    policy_url: str,
    policy_api_key: str,
    output_path: str,
) -> bool:
    """Export signed evidence via policy service API and verify signature."""
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

    os.environ["TOKEN_SERVICE_URL"] = token_url
    os.environ["TOKEN_SERVICE_API_KEY"] = token_api_key
    os.environ["POLICY_SERVICE_URL"] = policy_url
    os.environ["POLICY_SERVICE_API_KEY"] = policy_api_key

    print("1. Creating token + policy to block Gmail send...")
    result = create_token(token_url, token_api_key)
    if not result:
        print("   Failed. Ensure token service is running (docker compose up -d).", file=sys.stderr)
        return 1
    token, token_id = result
    print(f"   Token created (id: {token_id})")

    if not create_policy(policy_url, policy_api_key):
        return 1
    print("   Policy created")

    print("\n2. Running agent attempt -> blocked (show evidence_id)...")
    exit_code, output, evidence_id = run_agent(token)
    print(f"   {output.strip()}")
    if exit_code != 1:
        print("   Expected block from policy. Check policy service.", file=sys.stderr)
        return 1

    print("\n3. Revoking token mid-flow...")
    if not revoke_token(token_url, token_api_key, token_id):
        print("   Failed to revoke token.", file=sys.stderr)
        return 1
    print("   Token revoked")

    print("\n4. Running agent again -> blocked (token_revoked)...")
    exit_code2, output2, _ = run_agent(token)
    print(f"   {output2.strip()}")
    if exit_code2 != 1:
        print("   Expected block from revocation. SDK may need WebSocket.", file=sys.stderr)

    print("\n5. Export evidence package -> verify signature...")
    if evidence_id:
        evidence_path = "yc_demo_evidence.json"
        if export_and_verify_evidence(
            evidence_id, policy_url, policy_api_key, evidence_path
        ):
            print(f"   Evidence bundle exported to {evidence_path}")

    print("\n--- YC Demo complete ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
