"""Tests for GET /revocations/stats endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_revocations_stats_returns_connected_count_and_heartbeat(
    client: TestClient,
) -> None:
    """GET /revocations/stats returns connected_count and last_heartbeat."""
    resp = client.get("/revocations/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "connected_count" in data
    assert "last_heartbeat" in data
    assert isinstance(data["connected_count"], int)
    assert data["connected_count"] >= 0
    assert data["last_heartbeat"] is None or isinstance(data["last_heartbeat"], str)


def test_revocations_stats_requires_api_key() -> None:
    """GET /revocations/stats without API key returns 401."""
    from fastapi.testclient import TestClient

    from app.main import app

    no_auth_client = TestClient(app)
    resp = no_auth_client.get("/revocations/stats")
    assert resp.status_code == 401
