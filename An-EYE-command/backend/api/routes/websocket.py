from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from backend.websocket.manager import manager


router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            # Keep the connection alive while clients listen for broadcasts.
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
