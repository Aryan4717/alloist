"""RBAC tests: admin can revoke, developer can mint, viewer cannot."""

from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def api_key() -> str:
    return "dev-api-key"


@pytest.fixture(autouse=True)
def mock_settings(api_key: str):
    with patch("app.api.deps.get_settings") as mock:
        mock.return_value.TOKEN_SERVICE_API_KEY = api_key
        yield mock


@pytest.fixture
def client(api_key: str) -> TestClient:
    return TestClient(app, headers={"X-API-Key": api_key, "X-Org-Id": DEFAULT_ORG_ID})


def test_admin_can_revoke(client: TestClient) -> None:
    """Admin (legacy key) can revoke tokens."""
    token_id = uuid4()
    with patch("app.api.routes.tokens.revoke_token") as mock_revoke:
        mock_revoke.return_value = True
        resp = client.post("/tokens/revoke", json={"token_id": str(token_id)})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_revoke.assert_called_once()


def test_developer_can_mint(client: TestClient) -> None:
    """Developer can mint tokens (legacy key = admin, so can mint)."""
    with patch("app.api.routes.tokens.mint_token") as mock_mint:
        mock_mint.return_value = ("jwt...", uuid4(), __import__("datetime").datetime.now())
        resp = client.post(
            "/tokens",
            json={"subject": "dev", "scopes": ["read"], "ttl_seconds": 3600},
        )
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_viewer_can_list_tokens(client: TestClient) -> None:
    """Viewer can list tokens (legacy key = admin)."""
    with patch("app.api.routes.tokens.list_tokens") as mock_list:
        mock_list.return_value = ([], 0)
        resp = client.get("/tokens")
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_missing_x_org_id_uses_default(client: TestClient, api_key: str) -> None:
    """When X-Org-Id missing, default org is used (backward compat)."""
    no_org_client = TestClient(app, headers={"X-API-Key": api_key})
    with patch("app.api.routes.tokens.list_tokens") as mock_list:
        mock_list.return_value = ([], 0)
        resp = no_org_client.get("/tokens")
    assert resp.status_code == 200
    mock_list.assert_called_once()
    call_kwargs = mock_list.call_args[1]
    assert str(call_kwargs["org_id"]) == DEFAULT_ORG_ID
