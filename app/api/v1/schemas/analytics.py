from pydantic import BaseModel
import datetime

class ConversationBase(BaseModel):
    session_id: str
    user_message: str
    ai_response: str

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        orm_mode = True