"""Send push notifications via Expo Push API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from alloist_logging import get_logger

from app.models import PushToken

logger = get_logger("policy_service")

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def get_push_tokens_for_org(db: Session, org_id: UUID) -> list[str]:
    """Return list of Expo push tokens for org."""
    rows = db.query(PushToken).filter(PushToken.org_id == org_id).all()
    return [r.expo_push_token for r in rows if r.expo_push_token]


def send_consent_push(db: Session, org_id: UUID, payload: dict[str, Any]) -> None:
    """
    Send push notification to all registered devices for org.
    payload: { request_id, agent_name, action, metadata, risk_level }
    """
    tokens = get_push_tokens_for_org(db, org_id)
    if not tokens:
        return

    agent = payload.get("agent_name", "Agent")
    action = payload.get("action", {})
    action_str = f"{action.get('service', '')}.{action.get('name', '')}".strip(".") or "action"

    title = "Consent required"
    body = f"{agent} requested {action_str}"

    messages = [
        {
            "to": token,
            "title": title,
            "body": body,
            "data": payload,
            "sound": "default",
        }
        for token in tokens
    ]

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(EXPO_PUSH_URL, json=messages)
            if resp.status_code != 200:
                logger.warning("expo_push_failed", status_code=resp.status_code, response=resp.text)
            else:
                data = resp.json()
                if isinstance(data, dict) and data.get("data"):
                    for i, r in enumerate(data["data"]):
                        if isinstance(r, dict) and r.get("status") == "error":
                            logger.warning("expo_push_failed", token_index=i, message=r.get("message"))
    except Exception as e:
        logger.exception("expo_push_failed", error=str(e))
