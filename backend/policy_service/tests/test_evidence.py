"""Tests for evidence create, export, and verification."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.evidence import Evidence


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture(autouse=True)
def mock_settings(api_key: str):
    with patch("app.api.deps.get_settings") as mock_deps:
        mock_deps.return_value.POLICY_SERVICE_API_KEY = api_key
        yield mock_deps


@pytest.fixture(autouse=True)
def mock_evidence_signing_key():
    """Provide test signing keypair for evidence."""
    from app.services.evidence_service import generate_ed25519_keypair

    priv, pub = generate_ed25519_keypair()
    with patch("app.api.routes.evidence.get_public_key_b64") as mock_keys:
        with patch("app.services.evidence_service._get_signing_keypair") as mock_kp:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PrivateKey,
                Ed25519PublicKey,
            )
            import base64

            raw_priv = base64.b64decode(priv.encode("ascii"))
            raw_pub = base64.b64decode(pub.encode("ascii"))
            mock_kp.return_value = (
                Ed25519PrivateKey.from_private_bytes(raw_priv),
                Ed25519PublicKey.from_public_bytes(raw_pub),
            )
            mock_keys.return_value = pub
            yield mock_kp


@pytest.fixture
def client(api_key: str) -> TestClient:
    return TestClient(app, headers={"X-API-Key": api_key})


@pytest.fixture
def mock_db_evidence():
    """Mock DB that stores Evidence records."""
    evidence_store: dict = {}

    class FakeQuery:
        def __init__(self, model):
            self.model = model

        def all(self):
            return list(evidence_store.values())

    class FakeSession:
        def add(self, obj):
            if isinstance(obj, Evidence):
                evidence_store[str(obj.id)] = obj

        def commit(self):
            pass

        def refresh(self, obj):
            pass

        def get(self, model, pk):
            if model == Evidence:
                return evidence_store.get(str(pk))
            return None

        def query(self, model):
            return FakeQuery(model)

    return FakeSession()


def test_create_evidence_stores_and_signs(
    client: TestClient,
    mock_db_evidence,
    mock_evidence_signing_key,
) -> None:
    """POST /evidence/create stores record and signature verifies."""
    from app.api.deps import get_db

    def override_get_db():
        yield mock_db_evidence

    app.dependency_overrides[get_db] = override_get_db

    try:
        evidence_id = uuid4()
        resp = client.post(
            "/evidence/create",
            json={
                "evidence_id": str(evidence_id),
                "action_name": "stripe.charge",
                "token_snapshot": {"kid": "key_1", "token_id": str(uuid4()), "scopes": ["payments"]},
                "policy_id": str(uuid4()),
                "result": "deny",
                "runtime_metadata": {"reason": "Block large Stripe charges"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["evidence_id"] == str(evidence_id)

        # Verify we can export and signature is valid
        export_resp = client.post("/evidence/export", json={"evidence_id": str(evidence_id)})
        assert export_resp.status_code == 200
        data = export_resp.json()
        bundle = data["bundle"]
        assert "runtime_signature" in bundle
        assert bundle["result"] == "deny"
        assert bundle["action_name"] == "stripe.charge"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_export_returns_signed_bundle(
    client: TestClient,
    mock_db_evidence,
    mock_evidence_signing_key,
) -> None:
    """POST /evidence/export returns bundle with valid signature."""
    from app.api.deps import get_db

    def override_get_db():
        yield mock_db_evidence

    app.dependency_overrides[get_db] = override_get_db

    try:
        evidence_id = uuid4()
        client.post(
            "/evidence/create",
            json={
                "evidence_id": str(evidence_id),
                "action_name": "gmail.send",
                "token_snapshot": {"kid": "k1", "token_id": str(uuid4()), "scopes": []},
                "policy_id": None,
                "result": "deny",
                "runtime_metadata": {},
            },
        )
        export_resp = client.post("/evidence/export", json={"evidence_id": str(evidence_id)})
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert "bundle" in data
        assert "signature" in data
        assert "public_key" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_verify_script_valid_bundle(
    client: TestClient,
    mock_db_evidence,
    mock_evidence_signing_key,
) -> None:
    """verify_evidence.py exits 0 for valid bundle."""
    from app.api.deps import get_db

    def override_get_db():
        yield mock_db_evidence

    app.dependency_overrides[get_db] = override_get_db

    try:
        evidence_id = uuid4()
        client.post(
            "/evidence/create",
            json={
                "evidence_id": str(evidence_id),
                "action_name": "stripe.charge",
                "token_snapshot": {"kid": "k1", "token_id": str(uuid4()), "scopes": ["payments"]},
                "policy_id": str(uuid4()),
                "result": "deny",
                "runtime_metadata": {"reason": "test"},
            },
        )
        export_resp = client.post("/evidence/export", json={"evidence_id": str(evidence_id)})
        bundle = export_resp.json()["bundle"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bundle, f)
            bundle_path = Path(f.name)

        try:
            from scripts.verify_evidence import verify_bundle

            # Use public_key from bundle
            assert verify_bundle(bundle_path) is True
        finally:
            bundle_path.unlink()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_tamper_detection(
    client: TestClient,
    mock_db_evidence,
    mock_evidence_signing_key,
) -> None:
    """Modified bundle fails verification."""
    from app.api.deps import get_db

    def override_get_db():
        yield mock_db_evidence

    app.dependency_overrides[get_db] = override_get_db

    try:
        evidence_id = uuid4()
        client.post(
            "/evidence/create",
            json={
                "evidence_id": str(evidence_id),
                "action_name": "stripe.charge",
                "token_snapshot": {"kid": "k1", "token_id": str(uuid4()), "scopes": []},
                "policy_id": None,
                "result": "deny",
                "runtime_metadata": {},
            },
        )
        export_resp = client.post("/evidence/export", json={"evidence_id": str(evidence_id)})
        bundle = export_resp.json()["bundle"].copy()

        # Tamper: change result
        bundle["result"] = "allow"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(bundle, f)
            bundle_path = Path(f.name)

        try:
            from scripts.verify_evidence import verify_bundle

            assert verify_bundle(bundle_path) is False
        finally:
            bundle_path.unlink()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_export_nonexistent_returns_404(client: TestClient, mock_db_evidence) -> None:
    """POST /evidence/export returns 404 for unknown evidence_id."""
    from app.api.deps import get_db

    def override_get_db():
        yield mock_db_evidence

    app.dependency_overrides[get_db] = override_get_db

    try:
        resp = client.post(
            "/evidence/export",
            json={"evidence_id": str(uuid4())},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_evidence_keys(client: TestClient, mock_evidence_signing_key) -> None:
    """GET /evidence/keys returns public key."""
    resp = client.get("/evidence/keys")
    assert resp.status_code == 200
    data = resp.json()
    assert "public_key" in data
    assert len(data["public_key"]) > 0
