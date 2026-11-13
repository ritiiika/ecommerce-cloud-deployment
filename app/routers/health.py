"""Health, readiness, and metrics observability endpoints."""

import logging
import os
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

_START_TIME = time.time()


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
        raise HTTPException(status_code=503, detail="Database not reachable")


@router.get("/metrics", summary="Application metrics (Prometheus/JSON format)")
async def metrics(db: AsyncSession = Depends(get_db)):
    """
    Exposes application metrics (Stretch Goal in Assessment Brief):
    Uptime, process PID, environment, and DB status.
    """
    uptime_seconds = round(time.time() - _START_TIME, 2)
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    return {
        "service": "ecommerce-api",
        "uptime_seconds": uptime_seconds,
        "pid": os.getpid(),
        "database_connected": db_connected,
        "metrics": {
            "app_uptime_seconds": uptime_seconds,
            "database_status_up": 1 if db_connected else 0,
        },
    }
