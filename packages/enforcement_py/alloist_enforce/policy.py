"""Policy: action_name -> required scope mapping."""

from __future__ import annotations

ACTION_SCOPE_MAP = {
    "send_email": "email:send",
    "delete_user": "user:delete",
    "transfer_funds": "funds:transfer",
}


def check_policy(action_name: str | None, scopes: list[str]) -> dict:
    """
    Check if token scopes allow the action.
    Returns {allowed: True} or {allowed: False, reason: str}.
    """
    if not action_name:
        return {"allowed": True}

    required_scope = ACTION_SCOPE_MAP.get(action_name)
    if not required_scope:
        return {"allowed": True}

    has_scope = isinstance(scopes, list) and required_scope in scopes
    if not has_scope:
        return {"allowed": False, "reason": f"missing_scope:{required_scope}"}

    return {"allowed": True}
