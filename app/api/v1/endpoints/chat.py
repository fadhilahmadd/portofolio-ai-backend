import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.chat import ChatMessage
from app.services.chat_service import ChatService, get_chat_service
from app.core.database import get_session

router = APIRouter()

@router.post("/")
async def handle_chat(
    chat_message: ChatMessage,
    chat_service: ChatService = Depends(get_chat_service),
    db: AsyncSession = Depends(get_session),
):
    """
    Handles incoming chat messages by streaming the response back to the client.
    It uses Server-Sent Events (SSE) to send tokens as they are generated
    and a final message with suggested questions.
    """
    if not chat_message.message or not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = str(chat_message.session_id)

    try:
        response_generator = chat_service.stream_response(
            session_id=session_id,
            message=chat_message.message,
            db=db
        )
        return StreamingResponse(response_generator, media_type="text/event-stream")
    except Exception as e:
        print(f"An error occurred in the chat endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An internal server error occurred."
        )
