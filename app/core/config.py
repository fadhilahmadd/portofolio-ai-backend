import os
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    """
    PROJECT_NAME: str = "Portfolio Chatbot"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development" # 'development' or 'production'

    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["*"]

    GOOGLE_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()