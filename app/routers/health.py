"""Health and readiness check endpoints."""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", summary="Liveness check")
async def health():
    """Returns 200 if the application process is alive."""
    return {"status": "ok", "service": "ecommerce-api"}


@router.get("/readiness", summary="Readiness check")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Returns 200 if the app is ready to serve (DB reachable)."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not reachable")
