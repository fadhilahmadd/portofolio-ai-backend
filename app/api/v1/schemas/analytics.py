from pydantic import BaseModel, Field
import datetime
from typing import List, Optional

class ConversationBase(BaseModel):
    session_id: str
    user_message: str
    ai_response: str
    suggested_questions: Optional[List[str]] = None
    mailto: Optional[str] = None
    # --- ADDED FIELDS ---
    user_audio_path: Optional[str] = None
    ai_audio_path: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True