"""
Machine repository for data access operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.machine import MachineModel
from database.repository.base import BaseRepository


class MachineRepository(BaseRepository[MachineModel]):
    """Repository for machine data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MachineModel)

    async def get_by_fingerprint(self, fingerprint: str) -> Optional[MachineModel]:
        """Get a machine by its hardware fingerprint."""
        return await self.get_by_field("machine_fingerprint", fingerprint)

    async def get_machines_by_customer(self, customer_id: str) -> list[MachineModel]:
        """Get all machines for a customer."""
        return await self.get_all(filters={"customer_id": customer_id})

    async def get_machines_by_license(self, license_id: str) -> list[MachineModel]:
        """Get all machines registered under a license."""
        return await self.get_all(filters={"license_id": license_id})

    async def get_blacklisted_machines(self) -> list[MachineModel]:
        """Get all blacklisted machines."""
        return await self.get_all(filters={"is_blacklisted": True})

    async def get_active_machines(self) -> list[MachineModel]:
        """Get all active machines."""
        return await self.get_all(filters={"status": "active"})