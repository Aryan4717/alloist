"""Policy evaluation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.models.token_ref import TokenRef, TokenStatus


@dataclass
class EvaluationResult:
    allowed: bool
    policy_id: UUID | None
    reason: str | None
    consent_request_id: str | None = None


def _get_nested(obj: dict, path: str) -> Any:
    """Get value from dict using dot notation (e.g., metadata.amount)."""
    parts = path.split(".")
    current: Any = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def matches_policy(policy_rules: dict[str, Any], action: dict[str, Any]) -> bool:
    """
    Check if policy match applies to the action.
    match.service and match.action_name support '*' wildcard.
    """
    match = policy_rules.get("match") or {}
    service_pattern = match.get("service", "*")
    action_pattern = match.get("action_name", "*")

    action_service = action.get("service", "")
    action_name = action.get("name", "")

    def _matches(pattern: str, value: str) -> bool:
        if pattern == "*":
            return True
        return pattern == value

    return _matches(service_pattern, action_service) and _matches(
        action_pattern, action_name
    )


def evaluate_conditions(
    conditions: list[dict[str, Any]], context: dict[str, Any]
) -> bool:
    """
    Evaluate all conditions against context.
    Returns True if all conditions pass.
    Context: { "metadata": {...}, "token": { "subject", "scopes" } }
    """
    if not conditions:
        return True

    for cond in conditions:
        field = cond.get("field")
        operator = cond.get("operator")
        expected = cond.get("value")

        if field is None or operator is None:
            continue

        actual = _get_nested(context, field)
        if not _eval_condition(operator, actual, expected):
            return False

    return True


def _eval_condition(operator: str, actual: Any, expected: Any) -> bool:
    """Evaluate a single condition."""
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "gt":
        return actual is not None and expected is not None and actual > expected
    if operator == "gte":
        return actual is not None and expected is not None and actual >= expected
    if operator == "lt":
        return actual is not None and expected is not None and actual < expected
    if operator == "lte":
        return actual is not None and expected is not None and actual <= expected
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple)) else False
    if operator == "contains":
        return (
            expected in actual
            if isinstance(actual, (list, tuple, str))
            else (expected in actual if hasattr(actual, "__contains__") else False)
        )
    if operator == "not_contains":
        return not (
            expected in actual
            if isinstance(actual, (list, tuple, str))
            else (expected in actual if hasattr(actual, "__contains__") else False)
        )
    return False


def evaluate(
    org_id: UUID,
    token_id: UUID,
    action: dict[str, Any],
    db: Session,
) -> EvaluationResult:
    """
    Orchestrate policy evaluation.
    1. Validate token exists and is active (scoped to org)
    2. Load policies for org
    3. Evaluate each policy; first matching deny wins
    """
    token = (
        db.query(TokenRef)
        .filter(TokenRef.id == token_id, TokenRef.org_id == org_id)
        .first()
    )
    if not token or token.status != TokenStatus.active:
        return EvaluationResult(
            allowed=False,
            policy_id=None,
            reason="token_invalid_or_revoked",
        )

    context = {
        "metadata": action.get("metadata", {}),
        "token": {
            "subject": token.subject,
            "scopes": token.scopes or [],
        },
    }

    action_dict = {
        "service": action.get("service", ""),
        "name": action.get("name", ""),
        "metadata": action.get("metadata", {}),
    }

    policies = db.query(Policy).filter(Policy.org_id == org_id).all()

    for policy in policies:
        rules = policy.rules or {}
        if not matches_policy(rules, action_dict):
            continue

        conditions = rules.get("conditions") or []
        if not evaluate_conditions(conditions, context):
            continue

        effect = rules.get("effect", "allow")
        if effect == "deny":
            reason = _build_deny_reason(policy, action_dict, conditions, context)
            return EvaluationResult(
                allowed=False,
                policy_id=policy.id,
                reason=reason,
            )
        if effect == "require_consent":
            from app.consent_manager import consent_broadcaster

            agent_name = token.subject or "agent"
            request_id, _ = consent_broadcaster.create_consent_request(
                org_id=org_id,
                token_id=token_id,
                agent_name=agent_name,
                action=action_dict,
                metadata=action_dict.get("metadata", {}),
                risk_level="medium",
            )
            return EvaluationResult(
                allowed=False,
                policy_id=policy.id,
                reason="pending_consent",
                consent_request_id=request_id,
            )

    return EvaluationResult(
        allowed=True,
        policy_id=None,
        reason=None,
    )


def _build_deny_reason(
    policy: Policy,
    action: dict[str, Any],
    conditions: list[dict],
    context: dict,
) -> str:
    """Build human-readable reason for deny."""
    parts = [policy.name or str(policy.id)]
    metadata = action.get("metadata", {})
    for cond in conditions:
        field = cond.get("field", "")
        operator = cond.get("operator", "")
        value = cond.get("value")
        actual = _get_nested(context, field)
        if actual is not None and value is not None:
            if operator == "gt":
                parts.append(f"{field} {actual} exceeds threshold {value}")
            elif operator == "gte":
                parts.append(f"{field} {actual} meets or exceeds {value}")
            elif operator == "lt":
                parts.append(f"{field} {actual} below threshold {value}")
            else:
                parts.append(f"{field}={actual} {operator} {value}")
    return ": ".join(parts) if len(parts) > 1 else parts[0]
