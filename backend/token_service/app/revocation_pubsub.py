"""Redis Pub/Sub for revocation events."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable

from redis.asyncio import Redis

from app.config import get_settings

logger = logging.getLogger(__name__)

CHANNEL = "revocations"

_redis: Redis | None = None
_pubsub_task: asyncio.Task | None = None


async def get_redis() -> Redis | None:
    """Get Redis connection. Returns None if Redis unavailable."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        url = get_settings().REDIS_URL
        _redis = Redis.from_url(url, decode_responses=True)
        await _redis.ping()
        return _redis
    except Exception as e:
        logger.warning("Redis unavailable: %s", e)
        return None


async def publish_revocation(signed_payload: dict[str, Any]) -> bool:
    """Publish signed revocation payload to Redis channel. Returns True on success."""
    redis = await get_redis()
    if not redis:
        return False
    try:
        message = json.dumps(signed_payload)
        await redis.publish(CHANNEL, message)
        return True
    except Exception as e:
        logger.warning("Redis publish failed: %s", e)
        return False


async def subscribe_revocation(
    callback: Callable[[dict[str, Any]], Any],
) -> None:
    """
    Subscribe to revocation channel and call callback for each message.
    Runs until cancelled. Callback receives parsed payload dict.
    """
    redis = await get_redis()
    if not redis:
        return
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(CHANNEL)
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            data = message.get("data")
            if not data:
                continue
            try:
                payload = json.loads(data)
                await callback(payload)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Invalid revocation message: %s", e)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.warning("Revocation subscribe error: %s", e)
    finally:
        try:
            await pubsub.aclose()
        except Exception:
            pass


def start_revocation_subscriber(
    callback: Callable[[dict[str, Any]], Any],
) -> asyncio.Task | None:
    """Start background task subscribing to Redis. Returns task or None."""
    global _pubsub_task
    if _pubsub_task is not None and not _pubsub_task.done():
        return _pubsub_task

    async def _run() -> None:
        while True:
            try:
                await subscribe_revocation(callback)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Revocation subscriber error: %s", e)
                await asyncio.sleep(5)

    _pubsub_task = asyncio.create_task(_run())
    return _pubsub_task


async def close_redis() -> None:
    """Close Redis connection (for shutdown)."""
    global _redis, _pubsub_task
    if _pubsub_task and not _pubsub_task.done():
        _pubsub_task.cancel()
        try:
            await _pubsub_task
        except asyncio.CancelledError:
            pass
        _pubsub_task = None
    if _redis:
        await _redis.close()
        _redis = None
