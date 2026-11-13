
"""Product business logic service."""

import json
import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, StockUpdate

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _record_audit(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str = "admin",
        details: Optional[dict] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            actor=actor,
            details=json.dumps(details, default=str) if details else None,
        )
        self.db.add(event)
        return event

    async def get_audit_events(
        self, entity_id: uuid.UUID
    ) -> list[AuditEvent]:
        result = await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.entity_id == str(entity_id))
            .order_by(AuditEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def search(
        self, q: Optional[str], page: int, page_size: int
    ) -> Tuple[list[Product], int]:
        query = select(Product).where(Product.is_active.is_(True))

        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(
                    Product.name.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )

        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )

        return list(result.scalars().all()), total

    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        result = await self.db.execute(
            select(Product).where(Product.sku == sku)
        )
        return result.scalar_one_or_none()

    async def create(
        self, payload: ProductCreate, actor: str = "admin"
    ) -> Product:
        product = Product(
            id=uuid.uuid4(),
            **payload.model_dump(),
        )

        self.db.add(product)
        await self.db.flush()

        await self._record_audit(
            entity_type="product",
            entity_id=str(product.id),
            action="create_product",
            actor=actor,
            details={
                "sku": product.sku,
                "name": product.name,
                "stock": product.stock_quantity,
            },
        )

        await self.db.commit()
        await self.db.refresh(product)

        logger.info(
            "Product created: sku=%s id=%s actor=%s",
            product.sku,
            product.id,
            actor,
        )

        return product

    async def update(
        self,
        product_id: uuid.UUID,
        payload: ProductUpdate,
        actor: str = "admin",
    ) -> Optional[Product]:
        product = await self.get_by_id(product_id)

        if not product:
            return None

        updated_fields = payload.model_dump(exclude_unset=True)

        for field, value in updated_fields.items():
            setattr(product, field, value)

        await self._record_audit(
            entity_type="product",
            entity_id=str(product_id),
            action="update_product",
            actor=actor,
            details=updated_fields,
        )

        await self.db.commit()
        await self.db.refresh(product)

        logger.info(
            "Product updated: id=%s actor=%s",
            product_id,
            actor,
        )

        return product

    async def adjust_stock(
        self,
        product_id: uuid.UUID,
        payload: StockUpdate,
        actor: str = "admin",
    ) -> Optional[Product]:
        product = await self.get_by_id(product_id)

        if not product:
            return None

        new_qty = product.stock_quantity + payload.quantity_delta

        if new_qty < 0:
            raise ValueError(
                f"Stock cannot go negative. Current: "
                f"{product.stock_quantity}, "
                f"delta: {payload.quantity_delta}"
            )

        old_qty = product.stock_quantity
        product.stock_quantity = new_qty

        await self._record_audit(
            entity_type="product",
            entity_id=str(product_id),
            action="adjust_stock",
            actor=actor,
            details={
                "previous_stock": old_qty,
                "delta": payload.quantity_delta,
                "new_stock": new_qty,
                "reason": payload.reason,
            },
        )

        await self.db.commit()
        await self.db.refresh(product)

        logger.info(
            "Stock adjusted: id=%s delta=%d reason=%s new_qty=%d actor=%s",
            product_id,
            payload.quantity_delta,
            payload.reason,
            new_qty,
            actor,
        )

        return product
