"""Remote token validation API."""

from __future__ import annotations

import httpx


def validate_token_remote(
    token: str,
    api_url: str,
    api_key: str = "",
) -> dict | None:
    """
    Call POST /tokens/validate. Returns {valid, status, subject, scopes} or None on failure.
    """
    base = api_url.rstrip("/")
    url = f"{base}/tokens/validate"

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json={"token": token}, headers=headers)
        if not resp.is_success:
            return None
        data = resp.json()
        return {
            "valid": data.get("valid", False),
            "status": data.get("status", "revoked"),
            "subject": data.get("subject", ""),
            "scopes": data.get("scopes", []),
        }
    except Exception:
        return None
