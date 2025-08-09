from fastapi import APIRouter
from app.api.v1.endpoints import chat, resume

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chatbot"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
