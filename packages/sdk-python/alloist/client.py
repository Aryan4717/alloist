"""Alloist SDK client."""

import httpx

from alloist.config import get_api_key, get_policy_service_url
from alloist.exceptions import AlloistPolicyDeniedError


def enforce(action: str, metadata: dict | None = None) -> dict:
    """
    Check if action is allowed by Alloist policy.
    Returns response dict on allow.
    Raises AlloistPolicyDeniedError on deny.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Alloist not initialized. Call init(api_key=...) first.")

    url = f"{get_policy_service_url()}/enforce"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "action": action,
        "metadata": metadata or {},
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=body, headers=headers)

    if response.status_code == 403:
        raise AlloistPolicyDeniedError("Action blocked by Alloist policy")

    response.raise_for_status()
    data = response.json()

    if not data.get("allowed", True):
        raise AlloistPolicyDeniedError("Action blocked by Alloist policy")

    return data
