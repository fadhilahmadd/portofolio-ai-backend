from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """
    Dependency to validate the API key from the X-API-Key header.
    """
    if api_key_header == settings.ANALYTICS_API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )