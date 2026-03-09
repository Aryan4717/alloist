#!/usr/bin/env python3
"""
CLI orchestrator: create token, create policy (deny gmail.send), run demo agent.
Shows blocked result with evidence_id.
"""

import os
import sys
from pathlib import Path

# Ensure cognara_enforce is importable
_repo_root = Path(__file__).resolve().parents[3]
_enforcement_path = _repo_root / "packages" / "enforcement_py"
if _enforcement_path.exists():
    sys.path.insert(0, str(_enforcement_path))

import httpx

# Import after path setup
from cognara_enforce import create_enforcement


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
    """Create policy (deny gmail.send) via policy service. Returns True on success."""
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


def run_agent(token: str) -> tuple[int, str]:
    """Run demo agent. Returns (exit_code, output)."""
    from agent import run_agent as _run_agent

    # Capture stdout
    import io

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exit_code = _run_agent(token)
        output = sys.stdout.getvalue()
        return exit_code, output
    finally:
        sys.stdout = old_stdout


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

    print("2. Creating policy (deny gmail.send)...")
    if not create_policy(policy_url, policy_api_key):
        return 1
    print("   Policy created")

    print("3. Running demo agent (attempts gmail.send)...")
    # Set env for agent
    os.environ["TOKEN_SERVICE_URL"] = token_url
    os.environ["TOKEN_SERVICE_API_KEY"] = token_api_key
    os.environ["POLICY_SERVICE_URL"] = policy_url
    os.environ["POLICY_SERVICE_API_KEY"] = policy_api_key

    exit_code, output = run_agent(token)
    print(f"   {output.strip()}")

    if exit_code == 1:
        print("\nDemo complete: Agent was blocked by policy (expected).")
        print("Evidence ID shown above proves the enforcement intercept.")
    else:
        print("\nDemo complete: Agent was allowed (policy may not be active).")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
