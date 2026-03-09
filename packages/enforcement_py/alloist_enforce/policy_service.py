"""Remote policy evaluation via policy service API."""

from __future__ import annotations

import httpx


def evaluate_remote(
    token_id: str,
    action: dict[str, str | dict],
    policy_service_url: str,
    api_key: str = "",
) -> dict | None:
    """
    Call POST /policy/evaluate on the policy service.
    Returns {allowed: bool, policy_id?: str, reason?: str} or None on failure.
    action: { "service": str, "name": str, "metadata": dict }
    """
    base = policy_service_url.rstrip("/")
    url = f"{base}/policy/evaluate"

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                url,
                json={"token_id": token_id, "action": action},
                headers=headers,
            )
        if not resp.is_success:
            return None
        data = resp.json()
        return {
            "allowed": data.get("allowed", True),
            "policy_id": data.get("policy_id"),
            "reason": data.get("reason"),
        }
    except Exception:
        return None
