from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud import crud_conversation
from app.core.database import get_session
from app.api.v1.schemas.analytics import Conversation

router = APIRouter()

@router.get("/", response_model=List[Conversation])
async def read_conversations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    """
    Retrieve conversation logs.
    """
    if skip < 0 or limit <= 0 or limit > 500:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")
    conversations = await crud_conversation.get_conversations(db, skip=skip, limit=limit)
    return conversations