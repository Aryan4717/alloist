"""Integration tests for revoke endpoint publishing to Redis."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def test_revoke_publishes_to_redis_when_available(
    client: TestClient,
) -> None:
    """POST /tokens/revoke publishes signed payload to Redis when available."""
    token_id = uuid4()
    with (
        patch("app.api.routes.tokens.revoke_token") as mock_revoke,
        patch("app.api.routes.tokens.publish_revocation", new_callable=AsyncMock) as mock_publish,
    ):
        mock_publish.return_value = True
        resp = client.post("/tokens/revoke", json={"token_id": str(token_id)})

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_revoke.assert_called_once()
    mock_publish.assert_called_once()
    call_payload = mock_publish.call_args[0][0]
    assert call_payload["token_id"] == str(token_id)
    assert call_payload["event"] == "revoked"
    assert "signature" in call_payload


def test_revoke_falls_back_to_broadcast_when_redis_unavailable(
    client: TestClient,
) -> None:
    """POST /tokens/revoke falls back to direct broadcast when Redis unavailable."""
    token_id = uuid4()
    with (
        patch("app.api.routes.tokens.revoke_token"),
        patch("app.api.routes.tokens.publish_revocation", new_callable=AsyncMock) as mock_publish,
        patch(
            "app.api.routes.tokens.revocation_broadcaster.broadcast_revocation_payload",
            new_callable=AsyncMock,
        ) as mock_broadcast,
    ):
        mock_publish.return_value = False
        resp = client.post("/tokens/revoke", json={"token_id": str(token_id)})

    assert resp.status_code == 200
    mock_publish.assert_called_once()
    mock_broadcast.assert_called_once()
    call_payload = mock_broadcast.call_args[0][0]
    assert call_payload["token_id"] == str(token_id)
