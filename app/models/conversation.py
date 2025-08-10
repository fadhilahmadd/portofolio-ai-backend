from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base
import datetime

class Conversation(Base):
    """
    Database model for storing conversation logs.
    Includes a JSON field for suggested questions.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(String)
    ai_response = Column(String)
    suggested_questions = Column(JSON) # New field for analytics
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
