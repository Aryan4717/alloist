"""Create evidence records via policy service API."""

from __future__ import annotations

import jwt
import httpx


def create_evidence_remote(
    evidence_id: str,
    action_name: str,
    token_snapshot: dict,
    policy_id: str | None,
    result: str,
    runtime_metadata: dict | None,
    policy_service_url: str,
    api_key: str = "",
) -> bool:
    """
    Call POST /evidence/create on the policy service.
    Returns True on success, False on failure.
    """
    base = policy_service_url.rstrip("/")
    url = f"{base}/evidence/create"

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    payload = {
        "evidence_id": evidence_id,
        "action_name": action_name,
        "token_snapshot": token_snapshot,
        "policy_id": policy_id,
        "result": result,
        "runtime_metadata": runtime_metadata or {},
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        return resp.is_success
    except Exception:
        return False


def get_token_snapshot(token: str, jti: str, scopes: list) -> dict:
    """Build token_snapshot from JWT and decoded payload. kid from header, token_id=jti, scopes."""
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid") or "unknown"
    except Exception:
        kid = "unknown"
    return {"kid": kid, "token_id": jti, "scopes": scopes}
