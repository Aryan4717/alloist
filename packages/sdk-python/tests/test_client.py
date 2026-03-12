"""Unit tests for Alloist SDK."""

import pytest
from unittest.mock import MagicMock, patch

from alloist import init, enforce, AlloistPolicyDeniedError


@pytest.fixture(autouse=True)
def reset_config():
    """Reset SDK config before each test."""
    init(api_key="test-token", policy_service_url="http://localhost:8001")
    yield
    init(api_key="", policy_service_url="http://localhost:8001")


def test_enforce_returns_on_allow():
    """enforce() returns response dict when backend allows."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"allowed": True}
    mock_response.raise_for_status = MagicMock()

    with patch("alloist.client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = enforce(action="gmail.send", metadata={"to": "user@gmail.com"})

    assert result == {"allowed": True}
    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args[1]
    assert call_kwargs["json"] == {"action": "gmail.send", "metadata": {"to": "user@gmail.com"}}
    assert "Authorization" in call_kwargs["headers"]
    assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"


def test_enforce_raises_on_deny_403():
    """enforce() raises AlloistPolicyDeniedError when backend returns 403."""
    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch("alloist.client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(AlloistPolicyDeniedError, match="Action blocked by Alloist policy"):
            enforce(action="gmail.send", metadata={})


def test_enforce_raises_on_allowed_false():
    """enforce() raises when response has allowed=false (e.g. 200 with denied)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"allowed": False, "reason": "Policy denies gmail.send"}
    mock_response.raise_for_status = MagicMock()

    with patch("alloist.client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(AlloistPolicyDeniedError, match="Action blocked by Alloist policy"):
            enforce(action="gmail.send", metadata={})


def test_enforce_requires_init():
    """enforce() raises ValueError if init() not called."""
    init(api_key="")  # Reset to uninitialized

    with pytest.raises(ValueError, match="Alloist not initialized"):
        enforce(action="gmail.send", metadata={})


def test_init_stores_config():
    """init() stores api_key and policy_service_url."""
    init(api_key="my-token", policy_service_url="https://policy.example.com")

    from alloist.config import get_api_key, get_policy_service_url

    assert get_api_key() == "my-token"
    assert get_policy_service_url() == "https://policy.example.com"
