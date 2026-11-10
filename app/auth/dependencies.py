"""Admin API key authentication dependency."""
from fastapi import Header, HTTPException, status

from app.config import settings


async def require_admin(x_api_key: str = Header(..., alias="X-API-Key")):
    """Require a valid admin API key for protected endpoints."""
    if x_api_key != settings.API_KEY_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key
