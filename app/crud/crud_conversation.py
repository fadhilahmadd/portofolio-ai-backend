from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.conversation import Conversation
from app.api.v1.schemas.analytics import ConversationCreate

async def create_conversation(db: AsyncSession, conversation: ConversationCreate) -> Conversation:
    """
    Creates and saves a new conversation log to the database,
    including suggested questions, mailto links, and audio file paths.
    """
    db_conversation = Conversation(
        session_id=conversation.session_id,
        user_message=conversation.user_message,
        ai_response=conversation.ai_response,
        suggested_questions=conversation.suggested_questions,
        mailto=conversation.mailto,
        user_audio_path=conversation.user_audio_path,
        ai_audio_path=conversation.ai_audio_path,
    )
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation

async def get_conversations(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of conversation logs from the database.
    """
    result = await db.execute(select(Conversation).offset(skip).limit(limit))
    return result.scalars().all()