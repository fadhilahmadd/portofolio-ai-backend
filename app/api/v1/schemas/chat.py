from pydantic import BaseModel

class ChatMessage(BaseModel):
    """
    Schema for an incoming chat message.
    """
    message: str

class ChatResponse(BaseModel):
    """
    Schema for an outgoing chat response.
    """
    response: str
