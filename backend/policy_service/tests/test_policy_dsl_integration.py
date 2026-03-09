"""Integration tests: compile_dsl API, create policy with DSL."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.policy import Policy


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
    return TestClient(app, headers={"X-API-Key": api_key})


@pytest.fixture
def mock_db_session():
    policies: list[Policy] = []

    class FakeQuery:
        def __init__(self, model):
            self.model = model

        def all(self):
            return list(policies)

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return policies[0] if policies else None

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

        def delete(self, obj):
            if obj in policies:
                policies.remove(obj)

        def query(self, model):
            return FakeQuery(model)

    return FakeSession()


def test_compile_dsl_then_create_policy(client: TestClient, mock_db_session: MagicMock) -> None:
    """Compile DSL via API, create policy with compiled rules and dsl."""
    from app.api.deps import get_db

    def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        # 1. Compile DSL
        compile_resp = client.post(
            "/policy/compile_dsl",
            json={
                "rules": [
                    {
                        "id": "stripe_high_value",
                        "description": "Block charges > 1000",
                        "conditions": [
                            'action.service == "stripe"',
                            'action.name == "charge"',
                            "metadata.amount > 1000",
                        ],
                        "effect": "deny",
                    },
                ],
            },
        )
        assert compile_resp.status_code == 200
        data = compile_resp.json()
        assert data.get("errors") is None
        rules = data["rules"]
        assert rules["effect"] == "deny"
        assert rules["match"]["service"] == "stripe"

        # 2. Create policy with compiled rules and dsl
        dsl_payload = {
            "rules": [
                {
                    "id": "stripe_high_value",
                    "conditions": [
                        'action.service == "stripe"',
                        'action.name == "charge"',
                        "metadata.amount > 1000",
                    ],
                    "effect": "deny",
                },
            ],
        }
        create_resp = client.post(
            "/policy",
            json={
                "name": "Stripe high value block",
                "description": "From DSL",
                "rules": rules,
                "dsl": dsl_payload,
            },
        )
        assert create_resp.status_code == 200
        policy = create_resp.json()
        assert policy["name"] == "Stripe high value block"
        assert policy["rules"]["effect"] == "deny"
        assert policy.get("dsl") == dsl_payload
    finally:
        app.dependency_overrides.pop(get_db, None)
