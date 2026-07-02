"""
Product repository for data access operations.

Provides CRUD and specialized queries for products.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.product import ProductModel
from database.repository.base import BaseRepository


class ProductRepository(BaseRepository[ProductModel]):
    """Repository for product data access."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with ProductModel."""
        super().__init__(session, ProductModel)

    async def get_by_name(self, name: str) -> Optional[ProductModel]:
        """Get a product by its name."""
        return await self.get_by_field("name", name)

    async def get_active_products(self) -> list[ProductModel]:
        """Get all active (non-deleted) products."""
        return await self.get_all(filters={"is_deleted": False, "is_active": True})

    async def get_products_by_publisher(self, publisher: str) -> list[ProductModel]:
        """Get all products by a specific publisher."""
        return await self.get_all(filters={"publisher": publisher})