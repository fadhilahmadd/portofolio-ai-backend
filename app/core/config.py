import os
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl, PostgresDsn, ValidationInfo, field_validator

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    """
    PROJECT_NAME: str = "Portofolio Chatbot"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development" # 'development' or 'production'

    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["*"]

    GOOGLE_API_KEY: str | None = None
    ANALYTICS_API_KEY: str = "REMEMBER-CHANGE-THIS-IN-PROD-DUDE!"

    MAIN_LLM_MODEL: str = "gemini-2.5-pro"
    HELPER_LLM_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    
    AUDIO_DIR: str = "audio" 
    
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: PostgresDsn | None = None

    @field_validator("DATABASE_URL", mode='before')
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> any:
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()