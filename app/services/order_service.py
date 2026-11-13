"""Order business logic with concurrent idempotency protection and stock management."""
import hashlib
import json
import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _compute_payload_hash(self, payload: OrderCreate) -> str:
        """Compute deterministic SHA-256 fingerprint of the order payload."""
        sorted_items = sorted(
            [{"product_id": str(i.product_id), "quantity": i.quantity} for i in payload.items],
            key=lambda x: x["product_id"],
        )
        canonical_representation = json.dumps(
            {
                "customer_email": payload.customer_email.lower().strip(),
                "items": sorted_items,
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical_representation.encode("utf-8")).hexdigest()

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
        Creates an order with concurrent-safe idempotency.
        
        1. Checks if idempotency_key already exists.
        2. Validates request payload fingerprint: if a key is reused with different items/email,
           raises ValueError to prevent payload spoofing.
        3. Locks product rows (SELECT ... FOR UPDATE) to safely validate and decrement stock.
        4. Handles race conditions: if concurrent identical requests commit simultaneously,
           catches IntegrityError on unique constraint, rolls back, and returns the committed order.
        """
        current_hash = self._compute_payload_hash(payload)

        # 1. Fast check for existing order
        existing = await self._get_by_idempotency_key(payload.idempotency_key)
        if existing:
            if existing.request_hash and existing.request_hash != current_hash:
                raise ValueError(
                    f"Idempotency key '{payload.idempotency_key}' was already used for a different order payload"
                )
            return existing, False

        # 2. Acquire row-level locks and validate stock
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
                    id=uuid.uuid4(),
                    product_id=product.id,
                    product_sku=product.sku,
                    product_name=product.name,
                    quantity=item_req.quantity,
                    unit_price=unit_price,
                )
            )

            product.stock_quantity -= item_req.quantity

        order = Order(
            id=uuid.uuid4(),
            idempotency_key=payload.idempotency_key,
            request_hash=current_hash,
            customer_email=payload.customer_email,
            total_amount=round(total, 2),
            items=order_items,
        )
        self.db.add(order)

        try:
            await self.db.commit()
        except IntegrityError:
            # Concurrent race condition: another concurrent transaction committed this idempotency_key
            await self.db.rollback()
            existing_after_race = await self._get_by_idempotency_key(payload.idempotency_key)
            if existing_after_race:
                if existing_after_race.request_hash and existing_after_race.request_hash != current_hash:
                    raise ValueError(
                        f"Idempotency key '{payload.idempotency_key}' was already used for a different order payload"
                    )
                logger.info("Handled concurrent idempotency race for key=%s", payload.idempotency_key)
                return existing_after_race, False
            raise
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
