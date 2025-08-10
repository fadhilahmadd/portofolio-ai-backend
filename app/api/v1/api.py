from fastapi import APIRouter
from app.api.v1.endpoints import chat, analytics

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chatbot"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])