from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.security import decode_token
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/prs/{pr_id}")
async def pr_comments_ws(websocket: WebSocket, pr_id: UUID) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return
    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=4401, reason="Invalid token")
        return
    if payload.get("type") != "access":
        await websocket.close(code=4401, reason="Invalid token type")
        return

    await manager.connect(pr_id, websocket)
    try:
        while True:
            # clients only listen; ignore any incoming frames
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(pr_id, websocket)
    except Exception:
        await manager.disconnect(pr_id, websocket)
