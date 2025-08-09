from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    """
    Schema for an incoming chat message.
    """
    session_id: str
    message: str

class ChatResponse(BaseModel):
    """
    Schema for an outgoing chat response.
    Includes the main answer and optional suggested follow-up questions.
    """
    response: str
    suggested_questions: Optional[List[str]] = None
