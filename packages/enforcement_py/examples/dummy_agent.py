#!/usr/bin/env python3
"""
Dummy agent that wraps tool calls with enforcement.
Run with: python examples/dummy_agent.py <token>

Prerequisites:
- Token service running (docker-compose up)
- Valid token with scope "email:send" (from POST /tokens)
"""

import os
import sys

from alloist_enforce import create_enforcement


def run_agent(token: str) -> None:
    """Simulate agent calling send_email, guarded by enforcement check."""
    enforcement = create_enforcement(
        api_url=os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000"),
        api_key=os.environ.get("TOKEN_SERVICE_API_KEY", ""),
        fail_closed=True,
        high_risk_actions=["send_email"],
    )

    result = enforcement.check(
        token,
        action_name="send_email",
        metadata={"to": "user@example.com"},
    )

    if not result["allowed"]:
        print(f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})")
        return

    print("Agent executed send_email", {"to": "user@example.com", "evidence_id": result["evidence_id"]})
    enforcement.close()
    # In real app: actual_send_email(to="user@example.com", subject="...", body="...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dummy_agent.py <token>", file=sys.stderr)
        sys.exit(1)
    run_agent(sys.argv[1])
