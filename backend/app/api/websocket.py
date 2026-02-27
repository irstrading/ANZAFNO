# backend/app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
router = APIRouter()
@router.websocket("/ws/scanner")
async def websocket_scanner(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text("ping")
            import asyncio
            await asyncio.sleep(10)
    except WebSocketDisconnect: pass
