
"""Order business logic with concurrent idempotency protection and stock management."""

import hashlib
import json
import logging
import uuid
from decimal import Decimal
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
            [
                {
                    "product_id": str(item.product_id),
                    "quantity": item.quantity,
                }
                for item in payload.items
            ],
            key=lambda item: item["product_id"],
        )

        canonical_representation = json.dumps(
            {
                "customer_email": payload.customer_email.lower().strip(),
                "items": sorted_items,
            },
            sort_keys=True,
        )

        return hashlib.sha256(
            canonical_representation.encode("utf-8")
        ).hexdigest()

    def _validate_existing_order(
        self,
        existing: Order,
        current_hash: str,
        idempotency_key: str,
    ) -> None:
        """Reject reuse of an idempotency key with a different payload."""

        if (
            existing.request_hash
            and existing.request_hash != current_hash
        ):
            raise ValueError(
                f"Idempotency key '{idempotency_key}' "
                "was already used for a different order payload"
            )

    async def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )

        return result.scalar_one_or_none()

    async def _get_by_idempotency_key(
        self, key: str
    ) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.idempotency_key == key)
        )

        return result.scalar_one_or_none()

    async def create_order(
        self, payload: OrderCreate
    ) -> Tuple[Order, bool]:
        """
        Create an order with concurrency-safe idempotency.

        1. Check for an existing idempotency key.
        2. Validate the request fingerprint.
        3. Lock products in a consistent order.
        4. Recheck idempotency after acquiring locks.
        5. Validate stock and calculate prices using Decimal.
        6. Commit the order and inventory changes atomically.
        7. Handle concurrent unique-constraint conflicts.
        """

        current_hash = self._compute_payload_hash(payload)
        idempotency_key = payload.idempotency_key

        # STEP 1: Initial idempotency check
        existing = await self._get_by_idempotency_key(
            idempotency_key
        )

        if existing:
            self._validate_existing_order(
                existing,
                current_hash,
                idempotency_key,
            )
            return existing, False

        try:
            # STEP 2: Aggregate requested quantities by product.
            requested_quantities: dict[uuid.UUID, int] = {}

            for item in payload.items:
                requested_quantities[item.product_id] = (
                    requested_quantities.get(item.product_id, 0)
                    + item.quantity
                )

            # STEP 3: Lock products in deterministic order.
            product_ids = sorted(
                requested_quantities.keys(),
                key=str,
            )

            result = await self.db.execute(
                select(Product)
                .where(
                    Product.id.in_(product_ids),
                    Product.is_active.is_(True),
                )
                .order_by(Product.id)
                .with_for_update()
            )

            products = {
                product.id: product
                for product in result.scalars().all()
            }

            # STEP 4: Verify every requested product exists.
            for product_id in product_ids:
                if product_id not in products:
                    raise ValueError(
                        f"Product {product_id} not found or inactive"
                    )

            # STEP 5: Recheck idempotency after acquiring locks.
            # Another request may have completed while we were waiting.
            existing = await self._get_by_idempotency_key(
                idempotency_key
            )

            if existing:
                self._validate_existing_order(
                    existing,
                    current_hash,
                    idempotency_key,
                )

                # Release product locks before returning.
                await self.db.rollback()

                # Reload the order in a fresh transaction.
                existing = await self._get_by_idempotency_key(
                    idempotency_key
                )

                if existing is None:
                    raise RuntimeError(
                        "Previously detected order could not be retrieved"
                    )

                return existing, False

            # STEP 6: Validate aggregate stock requirements.
            for product_id, requested_quantity in (
                requested_quantities.items()
            ):
                product = products[product_id]

                if product.stock_quantity < requested_quantity:
                    raise ValueError(
                        f"Insufficient stock for '{product.name}'. "
                        f"Available: {product.stock_quantity}, "
                        f"requested: {requested_quantity}"
                    )

            # STEP 7: Create order items and calculate exact totals.
            order_items = []
            total = Decimal("0.00")

            for item_req in payload.items:
                product = products[item_req.product_id]

                unit_price = Decimal(str(product.price))

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

            # STEP 8: Deduct stock once per product.
            for product_id, requested_quantity in (
                requested_quantities.items()
            ):
                product = products[product_id]
                product.stock_quantity -= requested_quantity

            # STEP 9: Create the order.
            order = Order(
                id=uuid.uuid4(),
                idempotency_key=idempotency_key,
                request_hash=current_hash,
                customer_email=payload.customer_email,
                total_amount=total.quantize(Decimal("0.01")),
                items=order_items,
            )

            self.db.add(order)

            # STEP 10: Commit order and stock changes atomically.
            await self.db.commit()

        except IntegrityError:
            # A concurrent request may have committed the same key.
            await self.db.rollback()

            existing_after_race = await self._get_by_idempotency_key(
                idempotency_key
            )

            if existing_after_race:
                self._validate_existing_order(
                    existing_after_race,
                    current_hash,
                    idempotency_key,
                )

                logger.info(
                    "Handled concurrent idempotency conflict: key=%s",
                    idempotency_key,
                )

                return existing_after_race, False

            raise

        except Exception:
            await self.db.rollback()
            raise

        # STEP 11: Reload the committed order with its items.
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order.id)
        )

        order = result.scalar_one()

        logger.info(
            "Order created: id=%s email=%s total=%s items=%d",
            order.id,
            order.customer_email,
            order.total_amount,
            len(order.items),
        )

        return order, True
