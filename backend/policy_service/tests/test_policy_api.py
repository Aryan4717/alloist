"""API tests for policy endpoints."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.policy import Policy
from app.models.token_ref import TokenRef, TokenStatus
from app.services.evaluator import evaluate, EvaluationResult


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture(autouse=True)
def mock_settings(api_key: str):
    with patch("app.api.deps.get_settings") as mock:
        mock.return_value.POLICY_SERVICE_API_KEY = api_key
        yield mock


@pytest.fixture
def client(api_key: str) -> TestClient:
    return TestClient(app, headers={"X-API-Key": api_key})


@pytest.fixture
def mock_db_session():
    """Mock DB session with in-memory policy store for create/list."""
    policies: list[Policy] = []

    class FakeQuery:
        def __init__(self, model):
            self.model = model

        def all(self):
            return list(policies)

    class FakeSession:
        def add(self, obj):
            if isinstance(obj, Policy):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid4()
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = datetime.now(timezone.utc)
            policies.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            pass

        def get(self, model, pk):
            return None  # Override in tests for evaluate

        def query(self, model):
            return FakeQuery(model)

    return FakeSession()


def test_create_policy(client: TestClient, mock_db_session: MagicMock) -> None:
    """POST /policy creates and returns policy."""
    with patch("app.api.routes.policy.get_db") as mock_get_db:
        mock_get_db.return_value = iter([mock_db_session])

        # Need to replace the Depends(get_db) - use dependency_overrides
        from app.api.deps import get_db

        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/policy",
                json={
                    "name": "Block large Stripe charges",
                    "description": "Deny stripe.charge when amount > 1000",
                    "rules": {
                        "effect": "deny",
                        "match": {"service": "stripe", "action_name": "charge"},
                        "conditions": [
                            {
                                "field": "metadata.amount",
                                "operator": "gt",
                                "value": 1000,
                            }
                        ],
                    },
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Block large Stripe charges"
            assert "id" in data
            assert data["rules"]["effect"] == "deny"
            assert data["rules"]["match"]["service"] == "stripe"
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_evaluate_endpoint_deny(client: TestClient) -> None:
    """POST /policy/evaluate returns allowed: false for blocked action."""
    token_id = uuid4()
    policy_id = uuid4()

    with patch("app.api.routes.policy.evaluate") as mock_evaluate:
        mock_evaluate.return_value = EvaluationResult(
            allowed=False,
            policy_id=policy_id,
            reason="Block large Stripe charges: amount 1500 exceeds threshold 1000",
        )

        from app.api.deps import get_db

        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/policy/evaluate",
                json={
                    "token_id": str(token_id),
                    "action": {
                        "service": "stripe",
                        "name": "charge",
                        "metadata": {"amount": 1500, "currency": "usd"},
                    },
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is False
            assert data["policy_id"] == str(policy_id)
            assert "1500" in data["reason"]
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_evaluate_endpoint_allow(client: TestClient) -> None:
    """POST /policy/evaluate returns allowed: true when no policy matches."""
    token_id = uuid4()

    with patch("app.api.routes.policy.evaluate") as mock_evaluate:
        mock_evaluate.return_value = EvaluationResult(
            allowed=True,
            policy_id=None,
            reason=None,
        )

        from app.api.deps import get_db

        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/policy/evaluate",
                json={
                    "token_id": str(token_id),
                    "action": {
                        "service": "stripe",
                        "name": "charge",
                        "metadata": {"amount": 500},
                    },
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is True
            assert data["policy_id"] is None
            assert data["reason"] is None
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_evaluate_invalid_token(client: TestClient) -> None:
    """POST /policy/evaluate returns deny when token_id not found."""
    token_id = uuid4()

    with patch("app.api.routes.policy.evaluate") as mock_evaluate:
        mock_evaluate.return_value = EvaluationResult(
            allowed=False,
            policy_id=None,
            reason="token_invalid_or_revoked",
        )

        from app.api.deps import get_db

        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/policy/evaluate",
                json={
                    "token_id": str(token_id),
                    "action": {
                        "service": "stripe",
                        "name": "charge",
                        "metadata": {},
                    },
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is False
            assert data["reason"] == "token_invalid_or_revoked"
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_list_policies(client: TestClient) -> None:
    """GET /policy returns list of policies."""
    from uuid import UUID

    default_org = UUID("00000000-0000-0000-0000-000000000001")
    policy = Policy(
        id=uuid4(),
        org_id=default_org,
        name="Test policy",
        description="Test",
        rules={"effect": "deny", "match": {}, "conditions": []},
        created_at=datetime.now(timezone.utc),
    )

    from app.api.deps import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [policy]

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/policy")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Test policy"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_evaluate_requires_api_key() -> None:
    """POST /policy/evaluate without API key returns 401."""
    no_auth_client = TestClient(app)
    response = no_auth_client.post(
        "/policy/evaluate",
        json={
            "token_id": str(uuid4()),
            "action": {"service": "stripe", "name": "charge", "metadata": {}},
        },
    )
    assert response.status_code == 401
