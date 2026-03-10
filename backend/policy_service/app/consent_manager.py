"""Consent request broadcaster and pending storage for real-time AI action consent."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    websocket: WebSocket
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PendingConsent:
    request_id: str
    org_id: UUID
    token_id: UUID
    agent_name: str
    action: dict[str, Any]
    metadata: dict[str, Any]
    risk_level: str
    status: str  # "pending" | "approved" | "denied"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConsentBroadcaster:
    def __init__(self) -> None:
        self._connections: list[ConnectionInfo] = []
        self._pending: dict[str, PendingConsent] = {}

    async def connect(self, websocket: WebSocket) -> None:
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

    def create_consent_request(
        self,
        org_id: UUID,
        token_id: UUID,
        agent_name: str,
        action: dict[str, Any],
        metadata: dict[str, Any],
        risk_level: str = "medium",
    ) -> tuple[str, dict[str, Any]]:
        """Create pending consent, return (request_id, payload). Caller must broadcast payload."""
        request_id = str(uuid4())
        pending = PendingConsent(
            request_id=request_id,
            org_id=org_id,
            token_id=token_id,
            agent_name=agent_name,
            action=action,
            metadata=metadata,
            risk_level=risk_level,
            status="pending",
        )
        self._pending[request_id] = pending

        payload = {
            "type": "consent_request",
            "request_id": request_id,
            "agent_name": agent_name,
            "action": action,
            "metadata": metadata,
            "risk_level": risk_level,
        }
        return request_id, payload

    def get_pending(self, request_id: str) -> PendingConsent | None:
        return self._pending.get(request_id)

    def get_broadcast_payload(self, request_id: str) -> dict[str, Any] | None:
        """Get payload for broadcasting (for async broadcast by route)."""
        pending = self._pending.get(request_id)
        if not pending:
            return None
        return {
            "type": "consent_request",
            "request_id": request_id,
            "agent_name": pending.agent_name,
            "action": pending.action,
            "metadata": pending.metadata,
            "risk_level": pending.risk_level,
        }

    def set_decision(self, request_id: str, decision: str) -> bool:
        """Set decision (approve/deny). Returns True if was pending."""
        pending = self._pending.get(request_id)
        if not pending or pending.status != "pending":
            return False
        pending.status = "approved" if decision == "approve" else "denied"
        return True

    async def broadcast_consent_request(self, payload: dict[str, Any]) -> None:
        """Broadcast consent request to all connected WebSocket clients."""
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


consent_broadcaster = ConsentBroadcaster()
