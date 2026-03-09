"""WebSocket connection manager for revocation push."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from app.revocation_pubsub import start_revocation_subscriber
from app.revocation_signing import verify_revocation

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    websocket: WebSocket
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RevocationBroadcaster:
    def __init__(self) -> None:
        self._connections: list[ConnectionInfo] = []
        self._subscriber_started = False

    def _ensure_subscriber(self) -> None:
        if self._subscriber_started:
            return
        self._subscriber_started = True

        async def on_redis_message(payload: dict[str, Any]) -> None:
            if not verify_revocation(payload.copy()):
                logger.warning("Invalid revocation payload ignored")
                return
            token_id = payload.get("token_id")
            if token_id:
                await self.broadcast_revocation_payload(payload)

        start_revocation_subscriber(on_redis_message)

    async def connect(self, websocket: WebSocket) -> None:
        self._ensure_subscriber()
        await websocket.accept()
        self._connections.append(ConnectionInfo(websocket=websocket))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections = [c for c in self._connections if c.websocket != websocket]

    def update_heartbeat(self, websocket: WebSocket) -> None:
        now = datetime.now(timezone.utc)
        for c in self._connections:
            if c.websocket == websocket:
                c.last_heartbeat = now
                break

    @property
    def connected_count(self) -> int:
        return len(self._connections)

    @property
    def last_heartbeat(self) -> datetime | None:
        if not self._connections:
            return None
        return max(c.last_heartbeat for c in self._connections)

    async def broadcast_revocation(self, token_id: str) -> None:
        """Legacy: broadcast plain token_id (for backward compat). Prefer broadcast_revocation_payload."""
        message = json.dumps({"token_id": token_id, "event": "revoked"})
        await self._send_to_all(message)

    async def broadcast_revocation_payload(self, payload: dict[str, Any]) -> None:
        """Broadcast signed revocation payload to all connected clients."""
        message = json.dumps(payload)
        await self._send_to_all(message)

    async def _send_to_all(self, message: str) -> None:
        dead: list[WebSocket] = []
        for conn in self._connections:
            try:
                await conn.websocket.send_text(message)
            except Exception:
                dead.append(conn.websocket)
        for ws in dead:
            self.disconnect(ws)


revocation_broadcaster = RevocationBroadcaster()
