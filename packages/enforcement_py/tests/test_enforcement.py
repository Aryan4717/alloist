"""Tests for enforcement check - block/allow flows."""

import threading
import time
from unittest.mock import patch

import pytest

from cognara_enforce import create_enforcement
from cognara_enforce.api import validate_token_remote
from tests.conftest import make_test_token


def test_returns_blocked_for_revoked_token_from_api() -> None:
    token, jwks, jti = make_test_token({"scopes": ["email:send"], "jti": "revoked-jti"})

    def mock_validate(*args, **kwargs) -> dict:
        return {
            "valid": False,
            "status": "revoked",
            "subject": "user",
            "scopes": [],
        }

    with patch("cognara_enforce.enforcement.api.validate_token_remote", side_effect=mock_validate):
        enforcement = create_enforcement(
            api_url="http://localhost:9999",
            fail_closed=False,
            jwks_override=jwks,
        )
        result = enforcement.check(token, "send_email", {"to": "user@example.com"})
        enforcement.close()

    assert result["allowed"] is False
    assert result["reason"] == "token_revoked"
    assert "evidence_id" in result


def test_returns_allowed_for_valid_token_with_correct_scope() -> None:
    token, jwks, _ = make_test_token({"scopes": ["email:send"]})

    def mock_validate(*args, **kwargs) -> dict:
        return {
            "valid": True,
            "status": "active",
            "subject": "user",
            "scopes": ["email:send"],
        }

    with patch("cognara_enforce.enforcement.api.validate_token_remote", side_effect=mock_validate):
        enforcement = create_enforcement(
            api_url="http://localhost:9999",
            fail_closed=False,
            jwks_override=jwks,
        )
        result = enforcement.check(token, "send_email", {"to": "user@example.com"})
        enforcement.close()

    assert result["allowed"] is True
    assert "evidence_id" in result


def test_returns_blocked_when_policy_service_denies() -> None:
    """When policy_service_url is set and policy service returns allowed: false, block."""
    token, jwks, jti = make_test_token({"scopes": ["email:send"], "jti": "test-jti-123"})

    def mock_validate(*args, **kwargs) -> dict:
        return {
            "valid": True,
            "status": "active",
            "subject": "user",
            "scopes": ["email:send"],
        }

    def mock_policy_evaluate(*args, **kwargs) -> dict:
        return {"allowed": False, "policy_id": "p1", "reason": "Block Gmail send"}

    with (
        patch("cognara_enforce.enforcement.api.validate_token_remote", side_effect=mock_validate),
        patch(
            "cognara_enforce.enforcement.policy_service.evaluate_remote",
            side_effect=mock_policy_evaluate,
        ),
    ):
        enforcement = create_enforcement(
            api_url="http://localhost:9999",
            policy_service_url="http://localhost:8001",
            policy_service_api_key="dev-api-key",
            fail_closed=False,
            jwks_override=jwks,
        )
        result = enforcement.check(token, "gmail.send", {"to": "user@example.com"})
        enforcement.close()

    assert result["allowed"] is False
    assert result["reason"] == "Block Gmail send"
    assert "evidence_id" in result


def test_recheck_revoked_before_allowed_in_flight() -> None:
    """Fail-closed: re-check revoked_tokens before returning allowed (in-flight revocation)."""
    token, jwks, jti = make_test_token({"scopes": ["email:send"], "jti": "in-flight-jti"})
    revoked_tokens: set[str] = set()

    def slow_validate(*args, **kwargs) -> dict:
        time.sleep(0.2)
        return {
            "valid": True,
            "status": "active",
            "subject": "user",
            "scopes": ["email:send"],
        }

    result_holder: list = []

    def run_check():
        with (
            patch("cognara_enforce.enforcement.api.validate_token_remote", side_effect=slow_validate),
            patch("cognara_enforce.enforcement.websocket_.create_revocation_listener") as mock_ws,
        ):
            mock_ws.return_value = type("Listener", (), {"close": lambda: None})()
            enforcement = create_enforcement(
                api_url="http://localhost:9999",
                fail_closed=False,
                jwks_override=jwks,
                _test_revoked_tokens=revoked_tokens,
            )
            result_holder.append(
                enforcement.check(token, "send_email", {"to": "user@example.com"}),
            )
            enforcement.close()

    t = threading.Thread(target=run_check)
    t.start()
    time.sleep(0.05)
    revoked_tokens.add(jti)
    t.join()

    assert len(result_holder) == 1
    assert result_holder[0]["allowed"] is False
    assert result_holder[0]["reason"] == "token_revoked"
