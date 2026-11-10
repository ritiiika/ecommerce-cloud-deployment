"""Order business logic with idempotency and stock management."""
import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def _get_by_idempotency_key(self, key: str) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def create_order(self, payload: OrderCreate) -> Tuple[Order, bool]:
        """
        Returns (order, created). If idempotency_key already exists,
        returns the existing order and created=False.
        No duplicate stock deductions are made on replay.
        """
        existing = await self._get_by_idempotency_key(payload.idempotency_key)
        if existing:
            return existing, False

        order_items = []
        total = 0.0

        for item_req in payload.items:
            result = await self.db.execute(
                select(Product).where(
                    Product.id == item_req.product_id,
                    Product.is_active == True,
                ).with_for_update()
            )
            product: Optional[Product] = result.scalar_one_or_none()

            if not product:
                raise ValueError(f"Product {item_req.product_id} not found or inactive")

            if product.stock_quantity < item_req.quantity:
                raise ValueError(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.stock_quantity}, requested: {item_req.quantity}"
                )

            unit_price = float(product.price)
            total += unit_price * item_req.quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_sku=product.sku,
                    product_name=product.name,
                    quantity=item_req.quantity,
                    unit_price=unit_price,
                )
            )

            product.stock_quantity -= item_req.quantity

        order = Order(
            idempotency_key=payload.idempotency_key,
            customer_email=payload.customer_email,
            total_amount=round(total, 2),
            items=order_items,
        )
        self.db.add(order)

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        await self.db.refresh(order)
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order.id)
        )
        order = result.scalar_one()

        logger.info(
            "Order created: id=%s email=%s total=%.2f items=%d",
            order.id, order.customer_email, order.total_amount, len(order.items),
        )
        return order, True
