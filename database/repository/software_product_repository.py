"""
SoftwareProduct repository implementation.

This module provides data access operations for SoftwareProductModel
using the base repository pattern.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.software_product import SoftwareProductModel
from database.repository.base import BaseRepository
from core.logger import get_logger

logger = get_logger(__name__)


class SoftwareProductRepository(BaseRepository[SoftwareProductModel]):
    """Repository for SoftwareProduct CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session and model class."""
        super().__init__(session, SoftwareProductModel)

    async def get_by_app_id(self, app_id: str) -> Optional[SoftwareProductModel]:
        """Get a software product by its app_id (UUID)."""
        return await self.get_by_field("app_id", app_id, unique=True)  # type: ignore

    async def get_by_name(self, name: str) -> Optional[SoftwareProductModel]:
        """Get a software product by its name."""
        return await self.get_by_field("name", name, unique=True)  # type: ignore

    async def search_products(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SoftwareProductModel]:
        """Search software products by name, company, or exe_name."""
        query = select(SoftwareProductModel).where(
            or_(
                SoftwareProductModel.name.ilike(f"%{search_term}%"),
                SoftwareProductModel.company_name.ilike(f"%{search_term}%"),
                SoftwareProductModel.exe_name.ilike(f"%{search_term}%"),
                SoftwareProductModel.app_id.ilike(f"%{search_term}%"),
            )
        )
        query = query.offset(skip).limit(limit).order_by(SoftwareProductModel.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_products(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SoftwareProductModel]:
        """Get all active (non-deleted) software products."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            order_by="created_at",
            descending=True,
        )