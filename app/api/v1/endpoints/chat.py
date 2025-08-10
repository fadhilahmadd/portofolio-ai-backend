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
    to maintain conversation history and returns a response along with
    suggested follow-up questions to guide the conversation.
    """
    if not chat_message.message or not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if not chat_message.session_id or not chat_message.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID cannot be empty.")

    try:
        response_data = await chat_service.get_response(
            session_id=chat_message.session_id,
            message=chat_message.message
        )
        
        return ChatResponse(
            response=response_data["answer"],
            suggested_questions=response_data["suggested_questions"]
        )
    except Exception as e:
        print(f"An error occurred in the chat endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An internal server error occurred."
        )