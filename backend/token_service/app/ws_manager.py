"""WebSocket connection manager for revocation push."""
from fastapi import WebSocket
import json


class RevocationBroadcaster:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast_revocation(self, token_id: str) -> None:
        message = json.dumps({"token_id": token_id, "event": "revoked"})
        dead: list[WebSocket] = []
        for conn in self._connections:
            try:
                await conn.send_text(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


revocation_broadcaster = RevocationBroadcaster()
