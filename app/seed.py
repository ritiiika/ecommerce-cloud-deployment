"""Seed the database with initial products."""
import asyncio
import logging

from sqlalchemy import select
from app.database import AsyncSessionLocal, engine, Base
from app.models.product import Product

logger = logging.getLogger(__name__)

SEED_PRODUCTS = [
    {"sku": "LAPTOP-001", "name": 'Pro Laptop 15"', "description": "High-performance laptop", "price": 1299.99, "stock_quantity": 50},
    {"sku": "PHONE-001", "name": "Smartphone X12", "description": "Latest flagship phone", "price": 799.99, "stock_quantity": 100},
    {"sku": "TABLET-001", "name": "Tablet Pro 11", "description": "Lightweight tablet", "price": 599.99, "stock_quantity": 75},
    {"sku": "HEADPHONE-001", "name": "Noise-Cancel Headphones", "description": "Premium over-ear", "price": 249.99, "stock_quantity": 200},
    {"sku": "KEYBOARD-001", "name": "Mechanical Keyboard", "description": "RGB mechanical keyboard", "price": 129.99, "stock_quantity": 150},
    {"sku": "MOUSE-001", "name": "Wireless Mouse", "description": "Ergonomic wireless mouse", "price": 59.99, "stock_quantity": 300},
    {"sku": "MONITOR-001", "name": '27" 4K Monitor', "description": "Ultra-sharp 4K display", "price": 449.99, "stock_quantity": 60},
    {"sku": "SSD-001", "name": "1TB NVMe SSD", "description": "Fast NVMe solid state drive", "price": 89.99, "stock_quantity": 500},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for data in SEED_PRODUCTS:
            existing = await session.execute(
                select(Product).where(Product.sku == data["sku"])
            )
            if not existing.scalar_one_or_none():
                session.add(Product(**data))
                logger.info("Seeding product: %s", data["sku"])
        await session.commit()
    logger.info("Seed complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
