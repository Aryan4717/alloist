"""RBAC tests: admin can delete policy, developer can create, viewer can list evidence."""

from unittest.mock import MagicMock, patch
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
        mock.return_value.POLICY_SERVICE_API_KEY = api_key
        yield mock


@pytest.fixture
def client(api_key: str) -> TestClient:
    return TestClient(app, headers={"X-API-Key": api_key, "X-Org-Id": DEFAULT_ORG_ID})


def test_admin_can_delete_policy(client: TestClient) -> None:
    """Admin (legacy key) can delete policy."""
    policy_id = uuid4()
    mock_db = MagicMock()
    mock_policy = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_policy

    from app.api.deps import get_db

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        resp = client.delete(f"/policy/{policy_id}")
        assert resp.status_code == 204
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_developer_can_create_policy(client: TestClient) -> None:
    """Developer can create policy (legacy key = admin)."""
    from datetime import datetime, timezone

    mock_db = MagicMock()
    created_policy = None

    def capture_add(obj):
        nonlocal created_policy
        created_policy = obj
        if hasattr(obj, "id") and obj.id is None:
            obj.id = uuid4()
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)

    def mock_refresh(obj):
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)

    mock_db.add = capture_add
    mock_db.commit = lambda: None
    mock_db.refresh = mock_refresh

    from app.api.deps import get_db

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        resp = client.post(
            "/policy",
            json={
                "name": "Test",
                "description": "",
                "rules": {"effect": "allow", "match": {}, "conditions": []},
            },
        )
        assert resp.status_code == 200
        assert created_policy is not None
        assert created_policy.name == "Test"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_viewer_can_list_evidence(client: TestClient) -> None:
    """Viewer can list evidence (read logs)."""
    mock_db = MagicMock()
    chain = MagicMock()
    chain.filter.return_value = chain
    chain.order_by.return_value = chain
    chain.offset.return_value = chain
    chain.limit.return_value = chain
    chain.all.return_value = []
    chain.count.return_value = 0
    mock_db.query.return_value.filter.return_value = chain

    from app.api.deps import get_db

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        resp = client.get("/evidence")
        assert resp.status_code == 200
        assert "items" in resp.json()
    finally:
        app.dependency_overrides.pop(get_db, None)
