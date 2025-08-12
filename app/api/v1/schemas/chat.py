from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID

class ChatMessage(BaseModel):
    """
    Schema for an incoming chat message.
    """
    session_id: UUID
    message: str = Field(min_length=1, max_length=2000)

class StreamToken(BaseModel):
    """
    Schema for a single token in the response stream.
    """
    token: str

class FinalStreamResponse(BaseModel):
    """
    Schema for the final message in the stream, containing metadata.
    """
    suggested_questions: Optional[List[str]] = None
    mailto: Optional[str] = None

class UserIntent(str, Enum):
    """
    Enumeration for user intents.
    """
    RECRUITER = "recruiter"
    GENERAL_INQUIRY = "general_inquiry"
    CREATE_EMAIL = "create_email"