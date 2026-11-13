"""Admin API key authentication dependency with actor extraction."""
from typing import Optional
from fastapi import Header, HTTPException, status

from app.config import settings


async def require_admin(
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_admin_user: Optional[str] = Header("admin", alias="X-Admin-User"),
) -> str:
    """
    Require a valid admin API key for protected endpoints.
    Returns the authenticated admin actor identifier (defaults to 'admin' if not specified).
    """
    if x_api_key != settings.API_KEY_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_admin_user or "admin"
