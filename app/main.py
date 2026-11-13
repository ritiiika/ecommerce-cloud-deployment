"""E-Commerce Product & Order API – main application entry point."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.middleware.logging_middleware import StructuredLoggingMiddleware
from app.routers import health, orders, products

# Configure root logger for structured JSON output
logging.basicConfig(
    stream=sys.stdout,
    level=logging.getLevelName(settings.LOG_LEVEL),
    format="%(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (use Alembic migrations in production)."""
    if settings.APP_ENV not in ("test", "testing"):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables ensured")
        except Exception as exc:
            logger.warning("Database startup check skipped or failed: %s", exc)
    yield
    if settings.APP_ENV not in ("test", "testing"):
        try:
            await engine.dispose()
            logger.info("Database engine disposed")
        except Exception:
            pass


app = FastAPI(
    title="E-Commerce Product & Order API",
    version="1.0.0",
    description="Product search/details and order management with idempotency.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)

app.include_router(health.router, tags=["Health"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
