"""Tests for policy DSL compiler."""

import pytest

from app.dsl.compiler import compile_document, compile_rule, parse_condition
from app.schemas.policy_dsl import DslRule


def test_compile_stripe_high_value_rule() -> None:
    """Example DSL compiles to expected rules dict."""
    dsl = DslRule(
        id="stripe_high_value",
        description="Block charges > 1000 unless scope allow_payment",
        conditions=[
            'action.service == "stripe"',
            'action.name == "charge"',
            "metadata.amount > 1000",
        ],
        effect="deny",
    )
    result = compile_rule(dsl)
    assert result["effect"] == "deny"
    assert result["match"] == {"service": "stripe", "action_name": "charge"}
    assert result["conditions"] == [
        {"field": "metadata.amount", "operator": "gt", "value": 1000},
    ]


def test_compile_scope_contains() -> None:
    """'email:send' in token.scopes maps to contains operator."""
    dsl = DslRule(
        id="gmail_scope",
        description="Require email:send scope",
        conditions=[
            'action.service == "gmail"',
            'action.name == "send"',
            '"email:send" in token.scopes',
        ],
        effect="deny",
    )
    result = compile_rule(dsl)
    assert result["match"] == {"service": "gmail", "action_name": "send"}
    assert {"field": "token.scopes", "operator": "contains", "value": "email:send"} in result["conditions"]


def test_parse_condition_metadata_gt() -> None:
    """Parse metadata.amount > 1000."""
    c = parse_condition("metadata.amount > 1000")
    assert c == {"field": "metadata.amount", "operator": "gt", "value": 1000}


def test_parse_condition_in_token_scopes() -> None:
    """Parse 'email:send' in token.scopes."""
    c = parse_condition('"email:send" in token.scopes')
    assert c == {"field": "token.scopes", "operator": "contains", "value": "email:send"}


def test_parse_condition_single_quotes() -> None:
    """Parse with single-quoted literal."""
    c = parse_condition("metadata.currency == 'usd'")
    assert c == {"field": "metadata.currency", "operator": "eq", "value": "usd"}


def test_invalid_expression_returns_error() -> None:
    """Unknown operator or malformed LHS raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported"):
        parse_condition("metadata.amount ?? 1000")

    with pytest.raises(ValueError, match="Invalid"):
        parse_condition("metadata.amount >")


def test_compile_document_empty_rules() -> None:
    """compile_document with empty list returns errors."""
    rules, errors = compile_document([])
    assert rules == {}
    assert "At least one rule required" in errors[0]


def test_compile_document_success() -> None:
    """compile_document compiles first rule."""
    dsl_rules = [
        DslRule(
            id="test",
            description="Test",
            conditions=['action.service == "stripe"', "metadata.amount > 500"],
            effect="deny",
        ),
    ]
    rules, errors = compile_document(dsl_rules)
    assert errors == []
    assert rules["effect"] == "deny"
    assert rules["match"]["service"] == "stripe"
    assert len(rules["conditions"]) == 1
