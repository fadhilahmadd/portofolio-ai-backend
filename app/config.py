import os
from pydantic import AnyHttpUrl
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Application configuration settings.
    """
    PROJECT_NAME: str = "Portfolio Chatbot"
    API_V1_STR: str = "/api/v1"
    
    # Backend CORS origins
    # A list of origins that should be permitted to make cross-origin requests.
    # e.g. ["http://localhost:3000", "[https://your-frontend-domain.com](https://your-frontend-domain.com)"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

settings = Settings()