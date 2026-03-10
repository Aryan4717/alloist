"""Unit tests for policy evaluation logic."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.services.evaluator import (
    matches_policy,
    evaluate_conditions,
    evaluate,
    EvaluationResult,
)
from app.models.policy import Policy
from app.models.token_ref import TokenRef, TokenStatus


def test_matches_policy_service_action() -> None:
    """Policy matches when service and action_name match."""
    rules = {"match": {"service": "stripe", "action_name": "charge"}}
    action = {"service": "stripe", "name": "charge"}
    assert matches_policy(rules, action) is True

    rules2 = {"match": {"service": "stripe", "action_name": "refund"}}
    assert matches_policy(rules2, action) is False

    rules3 = {"match": {"service": "paypal", "action_name": "charge"}}
    assert matches_policy(rules3, action) is False


def test_matches_policy_wildcard() -> None:
    """Policy with * matches any service/action."""
    rules = {"match": {"service": "*", "action_name": "*"}}
    assert matches_policy(rules, {"service": "stripe", "name": "charge"}) is True
    assert matches_policy(rules, {"service": "any", "name": "any"}) is True

    rules2 = {"match": {"service": "stripe", "action_name": "*"}}
    assert matches_policy(rules2, {"service": "stripe", "name": "charge"}) is True
    assert matches_policy(rules2, {"service": "stripe", "name": "refund"}) is True
    assert matches_policy(rules2, {"service": "paypal", "name": "charge"}) is False


def test_evaluate_conditions_gt_lt_eq() -> None:
    """Condition operators gt, lt, eq work correctly."""
    context = {"metadata": {"amount": 500, "currency": "usd"}}

    assert evaluate_conditions(
        [{"field": "metadata.amount", "operator": "gt", "value": 1000}],
        context,
    ) is False
    assert evaluate_conditions(
        [{"field": "metadata.amount", "operator": "lt", "value": 1000}],
        context,
    ) is True
    assert evaluate_conditions(
        [{"field": "metadata.amount", "operator": "eq", "value": 500}],
        context,
    ) is True
    assert evaluate_conditions(
        [{"field": "metadata.amount", "operator": "gte", "value": 500}],
        context,
    ) is True
    assert evaluate_conditions(
        [{"field": "metadata.amount", "operator": "lte", "value": 500}],
        context,
    ) is True


def test_evaluate_conditions_empty() -> None:
    """Empty conditions always pass."""
    assert evaluate_conditions([], {"metadata": {}}) is True


def test_evaluate_conditions_not_contains() -> None:
    """not_contains operator denies when value not in list."""
    context = {"metadata": {}, "token": {"subject": "u1", "scopes": ["payments"]}}
    # Deny when allow_payment not in scopes
    assert evaluate_conditions(
        [{"field": "token.scopes", "operator": "not_contains", "value": "allow_payment"}],
        context,
    ) is True
    # Pass when allow_payment is in scopes
    context_with_scope = {"metadata": {}, "token": {"subject": "u1", "scopes": ["payments", "allow_payment"]}}
    assert evaluate_conditions(
        [{"field": "token.scopes", "operator": "not_contains", "value": "allow_payment"}],
        context_with_scope,
    ) is False


def test_evaluate_returns_deny_when_condition_met() -> None:
    """stripe.charge amount 1500 triggers deny."""
    from datetime import datetime, timezone

    org_id = UUID("00000000-0000-0000-0000-000000000001")
    token_id = uuid4()
    mock_token = TokenRef(
        id=token_id,
        org_id=org_id,
        subject="user1",
        scopes=["payments"],
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
        status=TokenStatus.active,
        signing_key_id="key1",
        token_value="jwt...",
    )
    policy = Policy(
        id=uuid4(),
        org_id=org_id,
        name="Block large Stripe charges",
        description="Deny stripe.charge when amount > 1000",
        rules={
            "effect": "deny",
            "match": {"service": "stripe", "action_name": "charge"},
            "conditions": [
                {"field": "metadata.amount", "operator": "gt", "value": 1000}
            ],
        },
        created_at=datetime.now(timezone.utc),
    )

    mock_db = MagicMock()
    mock_q = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token
    mock_db.query.return_value.filter.return_value.all.return_value = [policy]

    result = evaluate(
        org_id=org_id,
        token_id=token_id,
        action={
            "service": "stripe",
            "name": "charge",
            "metadata": {"amount": 1500, "currency": "usd"},
        },
        db=mock_db,
    )

    assert result.allowed is False
    assert result.policy_id == policy.id
    assert "1500" in (result.reason or "")
    assert "1000" in (result.reason or "")


def test_evaluate_returns_allow_when_no_match() -> None:
    """Unrelated action passes."""
    from datetime import datetime, timezone

    org_id = UUID("00000000-0000-0000-0000-000000000001")
    token_id = uuid4()
    mock_token = TokenRef(
        id=token_id,
        org_id=org_id,
        subject="user1",
        scopes=[],
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
        status=TokenStatus.active,
        signing_key_id="key1",
        token_value="jwt...",
    )
    policy = Policy(
        id=uuid4(),
        org_id=org_id,
        name="Block large Stripe charges",
        description="",
        rules={
            "effect": "deny",
            "match": {"service": "stripe", "action_name": "charge"},
            "conditions": [
                {"field": "metadata.amount", "operator": "gt", "value": 1000}
            ],
        },
        created_at=datetime.now(timezone.utc),
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token
    mock_db.query.return_value.filter.return_value.all.return_value = [policy]

    result = evaluate(
        org_id=org_id,
        token_id=token_id,
        action={
            "service": "paypal",
            "name": "charge",
            "metadata": {"amount": 2000},
        },
        db=mock_db,
    )

    assert result.allowed is True
    assert result.policy_id is None
    assert result.reason is None


def test_evaluate_returns_allow_when_condition_not_met() -> None:
    """stripe.charge amount 500 passes (below threshold)."""
    from datetime import datetime, timezone

    org_id = UUID("00000000-0000-0000-0000-000000000001")
    token_id = uuid4()
    mock_token = TokenRef(
        id=token_id,
        org_id=org_id,
        subject="user1",
        scopes=[],
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
        status=TokenStatus.active,
        signing_key_id="key1",
        token_value="jwt...",
    )
    policy = Policy(
        id=uuid4(),
        org_id=org_id,
        name="Block large Stripe charges",
        description="",
        rules={
            "effect": "deny",
            "match": {"service": "stripe", "action_name": "charge"},
            "conditions": [
                {"field": "metadata.amount", "operator": "gt", "value": 1000}
            ],
        },
        created_at=datetime.now(timezone.utc),
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token
    mock_db.query.return_value.filter.return_value.all.return_value = [policy]

    result = evaluate(
        org_id=org_id,
        token_id=token_id,
        action={
            "service": "stripe",
            "name": "charge",
            "metadata": {"amount": 500, "currency": "usd"},
        },
        db=mock_db,
    )

    assert result.allowed is True
    assert result.policy_id is None


def test_evaluate_invalid_token_returns_deny() -> None:
    """Returns deny when token not found."""
    org_id = UUID("00000000-0000-0000-0000-000000000001")
    token_id = uuid4()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = evaluate(
        org_id=org_id,
        token_id=token_id,
        action={"service": "stripe", "name": "charge", "metadata": {}},
        db=mock_db,
    )

    assert result.allowed is False
    assert result.reason == "token_invalid_or_revoked"


def test_evaluate_revoked_token_returns_deny() -> None:
    """Returns deny when token is revoked."""
    from datetime import datetime, timezone

    org_id = UUID("00000000-0000-0000-0000-000000000001")
    token_id = uuid4()
    mock_token = TokenRef(
        id=token_id,
        org_id=org_id,
        subject="user1",
        scopes=[],
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
        status=TokenStatus.revoked,
        signing_key_id="key1",
        token_value="jwt...",
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_token
    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = evaluate(
        org_id=org_id,
        token_id=token_id,
        action={"service": "stripe", "name": "charge", "metadata": {}},
        db=mock_db,
    )

    assert result.allowed is False
    assert result.reason == "token_invalid_or_revoked"
