"""Tests for auth endpoints."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import User

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def api_key() -> str:
    return "dev-api-key"


@pytest.fixture(autouse=True)
def mock_settings(api_key: str):
    mock = MagicMock()
    mock.return_value.TOKEN_SERVICE_API_KEY = api_key
    with patch("app.api.deps.get_settings", mock):
        with patch("app.api.routes.auth.get_settings", mock):
            yield mock


@pytest.fixture
def client(api_key: str) -> TestClient:
    return TestClient(app, headers={"X-API-Key": api_key, "X-Org-Id": DEFAULT_ORG_ID})


def test_saml_login_returns_501(client: TestClient) -> None:
    """GET /auth/saml/login returns 501."""
    resp = client.get("/auth/saml/login")
    assert resp.status_code == 501
    assert resp.json()["message"] == "SAML SSO is not yet implemented"


def test_saml_metadata_returns_xml(client: TestClient) -> None:
    """GET /auth/saml/metadata returns SAML metadata XML."""
    resp = client.get("/auth/saml/metadata")
    assert resp.status_code == 200
    assert "application/samlmetadata+xml" in resp.headers.get("content-type", "")
    assert "EntityDescriptor" in resp.text
    assert "SPSSODescriptor" in resp.text




def test_auth_me_without_auth_returns_401() -> None:
    """GET /auth/me without auth returns 401."""
    no_auth_client = TestClient(app)
    resp = no_auth_client.get("/auth/me")
    assert resp.status_code == 401


def test_auth_me_with_legacy_api_key() -> None:
    """GET /auth/me with legacy TOKEN_SERVICE_API_KEY returns user."""
    mock_settings = MagicMock()
    mock_settings.TOKEN_SERVICE_API_KEY = "dev-api-key"
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "admin@alloist.local"
    mock_user.name = "Admin"
    mock_org = MagicMock()
    mock_org.id = uuid4()
    mock_org.name = "Default"
    mock_ou = MagicMock()
    mock_ou.role.value = "admin"

    def query_side_effect(*models):
        q = MagicMock()
        if User in models:
            q.filter.return_value.first.return_value = mock_user
        else:
            q.join.return_value.filter.return_value.all.return_value = [
                (mock_org, mock_ou)
            ]
        return q

    mock_db.query.side_effect = query_side_effect

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.api.routes.auth.get_settings", return_value=mock_settings):
            from app.api.deps import get_db

            def override_get_db():
                yield mock_db

            app.dependency_overrides[get_db] = override_get_db
            try:
                client = TestClient(
                    app,
                    headers={"X-API-Key": "dev-api-key"},
                )
                resp = client.get("/auth/me")
                assert resp.status_code == 200
                data = resp.json()
                assert "user" in data
                assert data["user"]["email"] == "admin@alloist.local"
            finally:
                app.dependency_overrides.pop(get_db, None)
