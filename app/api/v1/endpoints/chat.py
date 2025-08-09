from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

from app.config import settings

router = APIRouter()

try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

INITIAL_PROMPT = """
You are a friendly and helpful chatbot for my personal portfolio website.
My name is Fadhil Ahmad Hidayat.
I am a Informathic Engineer with experience in Artificial Intelligence.
My resume is available at https://resume-fadhil-ahmad.tiiny.site.
You can find my projects on my GitHub: https://github.com/fadhilahmadd.
My social media links are:
- LinkedIn: https://www.linkedin.com/in/fadhil-ahmad-hidayat-604623139/
- Twitter: https://x.com/fadhil_ahmadd

When someone asks about me, my projects, or my skills, use this information to answer their questions.
Be conversational and engaging.
"""

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    chat_session = model.start_chat(history=[
        {"role": "user", "parts": [INITIAL_PROMPT]},
        {"role": "model", "parts": ["Great! I'm ready to help. What would you like to know?"]}
    ])
except Exception as e:
    chat_session = None
    print(f"Error initializing Gemini model: {e}")


@router.post("/", response_model=ChatResponse)
async def handle_chat(chat_message: ChatMessage):
    """
    Handles incoming chat messages, sends them to the Gemini API,
    and returns the model's response.
    """
    if not chat_session:
        raise HTTPException(
            status_code=500,
            detail="Chat model is not initialized. Check server logs for details."
        )
    
    if not chat_message.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        response = chat_session.send_message(chat_message.message)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred with the AI service: {str(e)}")