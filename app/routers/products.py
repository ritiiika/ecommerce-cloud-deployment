"""Product endpoints: search, detail, create (admin), stock update (admin), audit history."""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, StockUpdate
)
from app.schemas.audit import AuditEventResponse
from app.services.product_service import ProductService
from app.auth.dependencies import require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=ProductListResponse, summary="Search/list products")
async def list_products(
    q: Optional[str] = Query(None, description="Search term for name/SKU"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = ProductService(db)
    items, total = await svc.search(q=q, page=page, page_size=page_size)
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product details")
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ProductService(db)
    product = await svc.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product (admin)",
    dependencies=[Depends(require_admin)],
)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    svc = ProductService(db)
    return await svc.create(payload)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product (admin)",
    dependencies=[Depends(require_admin)],
)
async def update_product(
    product_id: uuid.UUID, payload: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    svc = ProductService(db)
    product = await svc.update(product_id, payload)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post(
    "/{product_id}/stock",
    response_model=ProductResponse,
    summary="Adjust stock (admin)",
    dependencies=[Depends(require_admin)],
)
async def adjust_stock(
    product_id: uuid.UUID, payload: StockUpdate, db: AsyncSession = Depends(get_db)
):
    svc = ProductService(db)
    try:
        product = await svc.adjust_stock(product_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get(
    "/{product_id}/audit",
    response_model=list[AuditEventResponse],
    summary="Get product audit events (admin)",
    dependencies=[Depends(require_admin)],
)
async def get_product_audit_events(
    product_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    svc = ProductService(db)
    return await svc.get_audit_events(product_id)
