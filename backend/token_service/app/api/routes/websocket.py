"""WebSocket endpoint for revocation push."""
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import verify_api_key
from app.ws_manager import revocation_broadcaster

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/revocations")
async def websocket_revocations(websocket: WebSocket) -> None:
    """WebSocket for real-time revocation updates. Clients receive signed payload with token_id, event, ts, nonce, signature."""
    await revocation_broadcaster.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            revocation_broadcaster.update_heartbeat(websocket)
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except (json.JSONDecodeError, TypeError):
                pass
    except WebSocketDisconnect:
        revocation_broadcaster.disconnect(websocket)


@router.get("/revocations/stats")
def get_revocations_stats(
    _: None = Depends(verify_api_key),
) -> dict:
    """Return connected WebSocket count and last heartbeat timestamp."""
    last = revocation_broadcaster.last_heartbeat
    return {
        "connected_count": revocation_broadcaster.connected_count,
        "last_heartbeat": last.isoformat() if last else None,
    }
