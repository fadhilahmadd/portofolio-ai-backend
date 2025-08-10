from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from uuid import UUID

class ChatMessage(BaseModel):
    """
    Schema for an incoming chat message.
    """
    session_id: UUID
    message: str

class ChatResponse(BaseModel):
    """
    Schema for an outgoing chat response.
    Includes the main answer and optional suggested follow-up questions.
    """
    response: str
    suggested_questions: Optional[List[str]] = None

class UserIntent(str, Enum):
    """
    Enumeration for user intents.
    """
    RECRUITER = "recruiter"
    GENERAL_INQUIRY = "general_inquiry"