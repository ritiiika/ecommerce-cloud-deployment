"""Order endpoints: create (idempotent), status."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import OrderService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order (idempotent)",
)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Create an order. If the same idempotency_key is submitted again,
    the existing order is returned without creating a duplicate or
    deducting stock again.
    """
    svc = OrderService(db)
    try:
        order, created = await svc.create_order(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not created:
        logger.info("Idempotent replay for key=%s", payload.idempotency_key)

    return order


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order status")
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = OrderService(db)
    order = await svc.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
