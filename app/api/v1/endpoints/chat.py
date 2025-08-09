from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.schemas.chat import ChatMessage, ChatResponse
from app.services.chat_service import ChatService, get_chat_service

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def handle_chat(
    chat_message: ChatMessage,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Asynchronously handles incoming chat messages. It uses a session_id
    to maintain conversation history for each user.
    """
    if not chat_message.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if not chat_message.session_id:
        raise HTTPException(status_code=400, detail="Session ID cannot be empty.")

    try:
        response_text = await chat_service.get_response(
            session_id=chat_message.session_id,
            message=chat_message.message
        )
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred: {str(e)}"
        )
