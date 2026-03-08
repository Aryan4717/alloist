"""WebSocket endpoint for revocation push."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import revocation_broadcaster

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/revocations")
async def websocket_revocations(websocket: WebSocket) -> None:
    """WebSocket for real-time revocation updates. Clients receive { token_id, event: 'revoked' }."""
    await revocation_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive; client can ping
    except WebSocketDisconnect:
        revocation_broadcaster.disconnect(websocket)
