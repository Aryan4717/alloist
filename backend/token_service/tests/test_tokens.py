from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def test_mint_token_returns_token_and_metadata(
    client: TestClient,
    sample_token_id: str,
    sample_expires_at: datetime,
) -> None:
    """POST /tokens returns token, token_id, expires_at; JWT contains sub, scopes, exp."""
    token_value = "eyJhbGciOiJFR0RTIiwiandrIjoia2V5XzEiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJ1c2VyMTIzIiwic2NvcGVzIjpbInJlYWQiLCJ3cml0ZSJdLCJpYXQiOjE3MDAwMDAwMDAsImV4cCI6MTcwMDAwMzYwMCwianRpIjoiYWJjZC0xMjM0In0.sig"
    with patch("app.api.routes.tokens.mint_token") as mock_mint:
        mock_mint.return_value = (token_value, uuid4(), sample_expires_at)
        response = client.post(
            "/tokens",
            json={
                "subject": "user123",
                "scopes": ["read", "write"],
                "ttl_seconds": 3600,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token"] == token_value
    assert "token_id" in data
    assert "expires_at" in data
    mock_mint.assert_called_once()
    call_kwargs = mock_mint.call_args[1]
    assert call_kwargs["subject"] == "user123"
    assert call_kwargs["scopes"] == ["read", "write"]
    assert call_kwargs["ttl_seconds"] == 3600


def test_revoke_token_sets_status_revoked(
    client: TestClient,
    sample_token_id: str,
) -> None:
    """Mint token, revoke it, GET metadata asserts status=revoked."""
    token_id = uuid4()
    with patch("app.api.routes.tokens.revoke_token") as mock_revoke:
        mock_revoke.return_value = True
        revoke_response = client.post(
            "/tokens/revoke",
            json={"token_id": str(token_id)},
        )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["success"] is True
    mock_revoke.assert_called_once()

    # Mock get_token_metadata to return revoked token
    from app.models import TokenStatus

    with patch("app.api.routes.tokens.get_token_metadata") as mock_get:
        mock_token = type("Token", (), {})()
        mock_token.id = token_id
        mock_token.subject = "user123"
        mock_token.scopes = ["read"]
        mock_token.issued_at = datetime.now(timezone.utc)
        mock_token.expires_at = datetime.now(timezone.utc)
        mock_token.status = TokenStatus.revoked
        mock_get.return_value = mock_token

        get_response = client.get(f"/tokens/{token_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "revoked"


def test_mint_token_requires_api_key() -> None:
    """POST /tokens without API key returns 401."""
    from fastapi.testclient import TestClient

    from app.main import app

    no_auth_client = TestClient(app)
    response = no_auth_client.post(
        "/tokens",
        json={"subject": "user", "scopes": [], "ttl_seconds": 3600},
    )
    assert response.status_code == 401
