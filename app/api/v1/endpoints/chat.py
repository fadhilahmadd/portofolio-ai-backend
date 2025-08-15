import json
import os
from typing import Optional
import aiofiles
from uuid import uuid4, UUID
from app.services.chat_service import AUDIO_DIR
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.services.chat_service import ChatService, get_chat_service
from app.services.audio_service import AudioService, get_audio_service
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter()

@router.post("/")
@limiter.limit("15/minute")
async def handle_chat(
    request: Request,
    background_tasks: BackgroundTasks,
    session_id: UUID = Form(...),
    message: str | None = Form(None),
    audio_file: UploadFile | None = File(None),
    include_audio_response: bool = Form(False),
    language: str = Form("en-US"),
    chat_service: ChatService = Depends(get_chat_service),
    audio_service: AudioService = Depends(get_audio_service),
):
    """
    Handles chat interactions with support for audio input (STT) and output (TTS).
    
    This endpoint accepts multipart/form-data. Provide either a text `message` or an `audio_file`.
    - If `audio_file` is sent, it is transcribed to text.
    - If `include_audio_response` is true, the chatbot's response is converted to an MP3.
    
    The response format depends on the `include_audio_response` flag:
    - If `False` (default): Returns a standard JSON response.
    - If `True`: Returns a `multipart/mixed` response with two parts: the JSON data and the MP3 audio data.
    """
    if not settings.GOOGLE_API_KEY:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable: missing Google API key")

    user_audio_bytes: Optional[bytes] = None
    
    if audio_file:
        user_audio_bytes = await audio_file.read()
        try:
            user_message = await audio_service.transcribe_audio(
                audio_bytes=user_audio_bytes,
                content_type=audio_file.content_type,
                language=language
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            print(f"Error during audio transcription: {e}")
            raise HTTPException(status_code=500, detail="Failed to process audio file.")
    elif message:
        user_message = message
    else:
        raise HTTPException(status_code=400, detail="Provide either a 'message' or an 'audio_file'.")

    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="Input message cannot be empty.")
    
    full_answer = ""
    suggested_questions = []
    mailto_link = None
    
    response_generator = chat_service.stream_response(
        session_id=str(session_id),
        message=user_message,
    )
    
    async for event in response_generator:
        if event.startswith("event: token"):
            data_str = event.split("data: ")[1].strip()
            data = json.loads(data_str)
            full_answer += data.get("token", "")
        elif event.startswith("event: final"):
            data_str = event.split("data: ")[1].strip()
            data = json.loads(data_str)
            suggested_questions = data.get("suggested_questions", [])
            mailto_link = data.get("mailto")

    response_json = {
        "ai_response": full_answer,
        "suggested_questions": suggested_questions,
        "mailto": mailto_link,
    }
    
    ai_audio_bytes: Optional[bytes] = None
    if include_audio_response:
        try:
            ai_audio_bytes = await audio_service.synthesize_speech(full_answer, language=language)
        except Exception as e:
            print(f"Error during speech synthesis: {e}")
            include_audio_response = False
    
    background_tasks.add_task(
        chat_service.log_conversation_task,
        session_id=str(session_id),
        user_message=user_message,
        ai_response=full_answer,
        suggested_questions=suggested_questions,
        mailto=mailto_link,
        user_audio_bytes=user_audio_bytes,
        ai_audio_bytes=ai_audio_bytes,
    )

    if not include_audio_response:
        return JSONResponse(content=response_json)

    try:
        audio_bytes = await audio_service.synthesize_speech(full_answer)
        
        filename = f"{session_id}_{uuid4()}.mp3"
        ai_audio_path = os.path.join(AUDIO_DIR, filename)
        async with aiofiles.open(ai_audio_path, "wb") as f:
            await f.write(audio_bytes)
            
    except Exception as e:
        print(f"Error during speech synthesis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate audio response.")

    async def multipart_generator():
        # The JSON data
        yield (
            b'--boundary\r\n'
            b'Content-Type: application/json\r\n\r\n' +
            json.dumps(response_json).encode('utf-8') +
            b'\r\n'
        )
        # The MP3 audio data
        yield (
            b'--boundary\r\n'
            b'Content-Type: audio/mpeg\r\n\r\n' +
            audio_bytes +
            b'\r\n'
        )
        yield b'--boundary--\r\n'

    return StreamingResponse(
        multipart_generator(),
        media_type="multipart/mixed; boundary=boundary"
    )