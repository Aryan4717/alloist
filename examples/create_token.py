#!/usr/bin/env python3
"""Create a capability token via the token service."""

import argparse
import os
import sys

try:
    import httpx
except ImportError:
    print("Requires httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)

TOKEN_SERVICE_URL = os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000")
TOKEN_SERVICE_API_KEY = os.environ.get("TOKEN_SERVICE_API_KEY", "dev-api-key")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an Alloist capability token")
    parser.add_argument("--subject", default="agent", help="Token subject (agent identifier)")
    parser.add_argument("--scopes", nargs="+", default=["email:send", "payments"], help="Capability scopes")
    parser.add_argument("--ttl", type=int, default=3600, help="Token TTL in seconds")
    args = parser.parse_args()

    base = TOKEN_SERVICE_URL.rstrip("/")
    url = f"{base}/tokens"
    headers = {"Content-Type": "application/json"}
    if TOKEN_SERVICE_API_KEY:
        headers["X-API-Key"] = TOKEN_SERVICE_API_KEY

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                url,
                json={
                    "subject": args.subject,
                    "scopes": args.scopes,
                    "ttl_seconds": args.ttl,
                },
                headers=headers,
            )
    except Exception as e:
        print(f"Failed to create token: {e}", file=sys.stderr)
        return 1

    if not resp.is_success:
        print(f"Token service error: {resp.status_code} {resp.text}", file=sys.stderr)
        return 1

    data = resp.json()
    token = data["token"]
    token_id = data["token_id"]
    expires_at = data.get("expires_at", "")

    print("Token created successfully")
    print(f"token_id: {token_id}")
    print(f"expires_at: {expires_at}")
    print(f"token: {token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
