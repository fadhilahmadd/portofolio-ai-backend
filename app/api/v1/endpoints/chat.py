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
    Handles incoming chat messages, sends them to the Gemini API via the
    ChatService, and returns the model's response.
    """
    if not chat_message.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        response_text = chat_service.get_response(chat_message.message)
        return {"response": response_text}
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred: {str(e)}"
        )
