"""Tests for audit log API and retention."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.audit_log import AuditLog
from app.services.evaluator import EvaluationResult

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


def test_log_audit_on_evaluate(client: TestClient) -> None:
    """Call evaluate, assert audit_log row created with correct action, result, org_id."""
    audit_logs: list[AuditLog] = []

    def capture_add(obj):
        if isinstance(obj, AuditLog):
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)
            audit_logs.append(obj)

    mock_db = MagicMock()
    mock_db.add = capture_add
    mock_db.commit = lambda: None
    mock_db.refresh = lambda obj: None

    from app.api.deps import get_db

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.api.routes.policy.evaluate") as mock_evaluate:
        mock_evaluate.return_value = EvaluationResult(
            allowed=False,
            policy_id=uuid4(),
            reason="Block large Stripe charges",
        )

        try:
            resp = client.post(
                "/policy/evaluate",
                json={
                    "token_id": str(uuid4()),
                    "action": {
                        "service": "stripe",
                        "name": "charge",
                        "metadata": {"amount": 1500, "currency": "usd"},
                    },
                },
            )
            assert resp.status_code == 200
            assert len(audit_logs) == 1
            log = audit_logs[0]
            assert log.action == "stripe.charge"
            assert log.result == "deny"
            assert str(log.org_id) == DEFAULT_ORG_ID
            assert log.metadata_["token_id"] is not None
            assert log.metadata_["action_metadata"] == {"amount": 1500, "currency": "usd"}
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_list_audit_logs(client: TestClient) -> None:
    """Create logs, GET /audit/logs with filters, assert response."""
    org_id = uuid4()
    log1 = AuditLog(
        id=uuid4(),
        org_id=org_id,
        action="stripe.charge",
        result="deny",
        metadata_={"token_id": str(uuid4()), "policy_id": str(uuid4())},
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.api.routes.audit.list_audit_logs", return_value=([log1], 1)):
        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        from app.api.deps import get_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            resp = client.get("/audit/logs?result=deny")
            assert resp.status_code == 200
            data = resp.json()
            assert "logs" in data
            assert data["total"] == 1
            assert len(data["logs"]) == 1
            assert data["logs"][0]["action"] == "stripe.charge"
            assert data["logs"][0]["result"] == "deny"
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_export_json(client: TestClient) -> None:
    """GET /audit/export?format=json, assert JSON structure."""
    org_id = uuid4()
    log_dict = {
        "id": str(uuid4()),
        "org_id": str(org_id),
        "action": "gmail.send",
        "result": "allow",
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with patch("app.api.routes.audit.export_audit_logs", return_value=[log_dict]):
        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        from app.api.deps import get_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            resp = client.get("/audit/export?format=json")
            assert resp.status_code == 200
            data = resp.json()
            assert "logs" in data
            assert "total" in data
            assert data["total"] == 1
            assert data["logs"][0]["action"] == "gmail.send"
            assert data["logs"][0]["result"] == "allow"
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_export_csv(client: TestClient) -> None:
    """GET /audit/export?format=csv, assert CSV with header."""
    org_id = uuid4()
    log_id = uuid4()
    csv_content = (
        "id,org_id,action,result,metadata,created_at\n"
        f"{log_id},{org_id},stripe.charge,deny,\"{{}}\",2026-01-01T00:00:00\n"
    )

    with patch("app.api.routes.audit.export_audit_logs", return_value=csv_content):
        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        from app.api.deps import get_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            resp = client.get("/audit/export?format=csv")
            assert resp.status_code == 200
            assert "text/csv" in resp.headers.get("content-type", "")
            assert "id,org_id,action,result,metadata,created_at" in resp.text
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_retention_cleanup() -> None:
    """Insert old log, run delete_expired_logs, assert deleted (mock or real DB)."""
    from app.models import AuditLog as AuditLogModel, Organization
    from app.services.audit_service import delete_expired_logs

    mock_db = MagicMock()
    mock_org = MagicMock()
    mock_org.id = uuid4()
    mock_org.retention_days = 7

    def query_side_effect(model):
        q = MagicMock()
        if model == Organization:
            q.all.return_value = [mock_org]
        elif model == AuditLogModel:
            q.filter.return_value.delete.return_value = 5
        return q

    mock_db.query.side_effect = query_side_effect

    result = delete_expired_logs(mock_db)
    mock_db.commit.assert_called_once()
    assert result == 5
