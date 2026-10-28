import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from app.logging import logger


class ConnectionManager:
    """Rooms of websocket clients, keyed by PR id."""

    def __init__(self) -> None:
        self._rooms: dict[UUID, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, pr_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(pr_id, set()).add(websocket)
        logger.info("ws_connected", pr_id=str(pr_id), clients=self.room_size(pr_id))

    async def disconnect(self, pr_id: UUID, websocket: WebSocket) -> None:
        async with self._lock:
            room = self._rooms.get(pr_id)
            if room is not None:
                room.discard(websocket)
                if not room:
                    self._rooms.pop(pr_id, None)
        logger.info("ws_disconnected", pr_id=str(pr_id), clients=self.room_size(pr_id))

    def room_size(self, pr_id: UUID) -> int:
        return len(self._rooms.get(pr_id, ()))

    async def broadcast(self, pr_id: UUID, message: dict[str, Any]) -> None:
        async with self._lock:
            room = list(self._rooms.get(pr_id, ()))
        if not room:
            return
        text = json.dumps(message)
        for websocket in room:
            try:
                await websocket.send_text(text)
            except Exception:
                await self.disconnect(pr_id, websocket)


manager = ConnectionManager()
