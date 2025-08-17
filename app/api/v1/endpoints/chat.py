import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

from app.services.chat_service import ChatService, get_chat_service
from app.services.audio_service import AudioService, get_audio_service
from app.core.limiter import limiter

router = APIRouter()

logger = logging.getLogger(__name__)

async def _sse_generator(
    session_id: str, 
    user_message: str, 
    chat_service: ChatService,
    background_tasks: BackgroundTasks,
    user_audio_bytes: Optional[bytes]
) -> AsyncGenerator[str, None]:
    """
    Yields Server-Sent Events for the RAG chat response stream and logs the final result.
    """
    full_answer = ""
    suggested_questions = []
    mailto_link = None
    
    response_generator = chat_service.stream_rag_response(
        session_id=session_id,
        message=user_message,
    )
    
    try:
        async for event in response_generator:
            yield event
            
            if event.startswith("event: token"):
                data = json.loads(event.split("data: ", 1)[1])
                full_answer += data.get("token", "")
            elif event.startswith("event: final"):
                data = json.loads(event.split("data: ", 1)[1])
                suggested_questions = data.get("suggested_questions", [])
                mailto_link = data.get("mailto")
    
    except asyncio.CancelledError:
        logger.error("Client disconnected, closing stream for session %s.", session_id)
    finally:
        if user_message and full_answer:
            background_tasks.add_task(
                chat_service.log_conversation_task,
                session_id=session_id,
                user_message=user_message,
                ai_response=full_answer,
                suggested_questions=suggested_questions,
                mailto=mailto_link,
                user_audio_bytes=user_audio_bytes,
                ai_audio_path=None, 
            )

@router.post("/")
@limiter.limit("15/minute")
async def handle_chat(
    request: Request,
    background_tasks: BackgroundTasks,
    session_id: UUID = Form(...),
    message: str | None = Form(None),
    audio_file: UploadFile | None = File(None),
    language: str = Form("en-US"),
    chat_service: ChatService = Depends(get_chat_service),
    audio_service: AudioService = Depends(get_audio_service),
):
    """
    Handles chat interactions by streaming text responses using SSE.
    """
    user_audio_bytes: Optional[bytes] = None
    user_message = ""

    if audio_file:
        user_audio_bytes = await audio_file.read()
        try:
            user_message = await audio_service.transcribe_audio(
                audio_bytes=user_audio_bytes,
                content_type=audio_file.content_type,
                language=language
            )
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail="Failed to process audio file.")
    elif message:
        user_message = message
    else:
        raise HTTPException(status_code=400, detail="Provide either a 'message' or an 'audio_file'.")

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Input message cannot be empty.")

    return StreamingResponse(
        _sse_generator(
            str(session_id),
            user_message,
            chat_service,
            background_tasks,
            user_audio_bytes,
        ),
        media_type="text/event-stream",
    )