"""Unit tests for revocation Redis pub/sub."""

from unittest.mock import AsyncMock, patch

import pytest

from app.revocation_pubsub import publish_revocation, subscribe_revocation


@pytest.mark.asyncio
async def test_publish_revocation_returns_false_when_redis_unavailable() -> None:
    """publish_revocation returns False when Redis is unavailable."""
    with patch("app.revocation_pubsub.get_redis", return_value=None):
        result = await publish_revocation({"token_id": "t1", "event": "revoked"})
    assert result is False


@pytest.mark.asyncio
async def test_publish_revocation_returns_true_on_success() -> None:
    """publish_revocation returns True when Redis publish succeeds."""
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock(return_value=1)

    with patch("app.revocation_pubsub.get_redis", return_value=mock_redis):
        result = await publish_revocation({"token_id": "t1", "event": "revoked"})

    assert result is True
    mock_redis.publish.assert_called_once()


@pytest.mark.asyncio
async def test_publish_revocation_returns_false_on_exception() -> None:
    """publish_revocation returns False when Redis publish raises."""
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock(side_effect=Exception("redis error"))

    with patch("app.revocation_pubsub.get_redis", return_value=mock_redis):
        result = await publish_revocation({"token_id": "t1", "event": "revoked"})

    assert result is False
