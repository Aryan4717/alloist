#!/usr/bin/env python3
"""Apply policies from examples/policies.json to the policy service."""

import json
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Requires httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)

POLICY_SERVICE_URL = os.environ.get("POLICY_SERVICE_URL", "http://localhost:8001")
POLICY_SERVICE_API_KEY = os.environ.get("POLICY_SERVICE_API_KEY", "dev-api-key")

SCRIPT_DIR = Path(__file__).resolve().parent
POLICIES_FILE = SCRIPT_DIR / "policies.json"


def main() -> int:
    if not POLICIES_FILE.exists():
        print(f"policies.json not found: {POLICIES_FILE}", file=sys.stderr)
        return 1

    with open(POLICIES_FILE) as f:
        policies = json.load(f)

    if not isinstance(policies, list):
        print("policies.json must be an array of policy objects", file=sys.stderr)
        return 1

    base = POLICY_SERVICE_URL.rstrip("/")
    url = f"{base}/policy"
    headers = {"Content-Type": "application/json"}
    if POLICY_SERVICE_API_KEY:
        headers["X-API-Key"] = POLICY_SERVICE_API_KEY

    for i, p in enumerate(policies):
        name = p.get("name", f"Policy {i+1}")
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=p, headers=headers)
            if resp.is_success:
                print(f"Created: {name}")
            else:
                print(f"Failed {name}: {resp.status_code} {resp.text}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Error applying {name}: {e}", file=sys.stderr)
            return 1

    print(f"Applied {len(policies)} policies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
