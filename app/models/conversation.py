from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base
import datetime

class Conversation(Base):
    """
    Database model for storing conversation logs.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(String)
    ai_response = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)