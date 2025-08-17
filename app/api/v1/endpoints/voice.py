from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.voice_service import VoiceServiceManager
import json

router = APIRouter()
voice_manager = VoiceServiceManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await voice_manager.handle_message(session_id, message, websocket)
    except WebSocketDisconnect:
        await voice_manager.cleanup(session_id)
        print(f"Client disconnected: {session_id}")