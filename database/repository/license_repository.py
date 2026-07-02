"""
License repository for data access operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.license import LicenseModel
from database.repository.base import BaseRepository
from core.constants import LicenseType, ActivationStatus


class LicenseRepository(BaseRepository[LicenseModel]):
    """Repository for license data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, LicenseModel)

    async def get_by_license_key(self, license_key: str) -> Optional[LicenseModel]:
        """Get a license by its key."""
        return await self.get_by_field("license_key", license_key)

    async def get_licenses_by_customer(self, customer_id: str) -> list[LicenseModel]:
        """Get all licenses for a customer."""
        return await self.get_all(filters={"customer_id": customer_id})

    async def get_licenses_by_product(self, product_id: str) -> list[LicenseModel]:
        """Get all licenses for a product."""
        return await self.get_all(filters={"product_id": product_id})

    async def get_expired_licenses(self) -> list[LicenseModel]:
        """Get all expired licenses."""
        query = select(LicenseModel).where(
            and_(
                LicenseModel.is_perpetual == False,
                LicenseModel.expires_at < datetime.utcnow(),
                LicenseModel.is_revoked == False,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_licenses(self) -> list[LicenseModel]:
        """Get all active licenses."""
        return await self.get_all(filters={"status": ActivationStatus.ACTIVATED, "is_revoked": False})

    async def get_licenses_by_type(self, license_type: LicenseType) -> list[LicenseModel]:
        """Get all licenses of a specific type."""
        return await self.get_all(filters={"license_type": license_type})