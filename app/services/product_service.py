"""Product business logic service."""
import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, StockUpdate

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self, q: Optional[str], page: int, page_size: int
    ) -> Tuple[list[Product], int]:
        query = select(Product).where(Product.is_active == True)
        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(Product.name.ilike(pattern), Product.sku.ilike(pattern))
            )
        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

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

    async def create(self, payload: ProductCreate) -> Product:
        product = Product(**payload.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        logger.info("Product created: sku=%s id=%s", product.sku, product.id)
        return product

    async def update(self, product_id: uuid.UUID, payload: ProductUpdate) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await self.db.commit()
        await self.db.refresh(product)
        logger.info("Product updated: id=%s", product_id)
        return product

    async def adjust_stock(self, product_id: uuid.UUID, payload: StockUpdate) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        new_qty = product.stock_quantity + payload.quantity_delta
        if new_qty < 0:
            raise ValueError(
                f"Stock cannot go negative. Current: {product.stock_quantity}, delta: {payload.quantity_delta}"
            )
        product.stock_quantity = new_qty
        await self.db.commit()
        await self.db.refresh(product)
        logger.info(
            "Stock adjusted: id=%s delta=%d reason=%s new_qty=%d",
            product_id, payload.quantity_delta, payload.reason, new_qty,
        )
        return product
