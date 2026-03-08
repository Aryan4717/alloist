from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture(autouse=True)
def mock_settings(api_key: str):
    """Inject test API key into settings."""
    with patch("app.api.deps.get_settings") as mock:
        mock.return_value.TOKEN_SERVICE_API_KEY = api_key
        yield mock


@pytest.fixture
def client(api_key: str) -> TestClient:
    """Test client with API key header."""
    return TestClient(app, headers={"X-API-Key": api_key})


@pytest.fixture
def sample_token_id() -> str:
    return str(uuid4())


@pytest.fixture
def sample_expires_at() -> datetime:
    return datetime.now(timezone.utc)
