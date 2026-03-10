"""Tests for api module."""

from unittest.mock import patch

import pytest

from alloist_enforce.api import validate_token_remote


def test_returns_data_when_api_valid() -> None:
    with patch("httpx.Client") as mock_client:
        mock_resp = mock_client.return_value.__enter__.return_value.post.return_value
        mock_resp.is_success = True
        mock_resp.json.return_value = {
            "valid": True,
            "status": "active",
            "subject": "user1",
            "scopes": ["email:send"],
            "jti": "abc-123",
        }
        result = validate_token_remote("token", "http://localhost:9999", "")
    assert result["valid"] is True
    assert result["status"] == "active"
    assert result["scopes"] == ["email:send"]


def test_returns_revoked_when_api_revoked() -> None:
    with patch("httpx.Client") as mock_client:
        mock_resp = mock_client.return_value.__enter__.return_value.post.return_value
        mock_resp.is_success = True
        mock_resp.json.return_value = {
            "valid": False,
            "status": "revoked",
            "subject": "user1",
            "scopes": [],
            "jti": "xyz",
        }
        result = validate_token_remote("token", "http://localhost:9999", "")
    assert result["valid"] is False
    assert result["status"] == "revoked"


def test_returns_none_when_request_fails() -> None:
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception("network error")
        result = validate_token_remote("token", "http://localhost:9999", "")
    assert result is None
