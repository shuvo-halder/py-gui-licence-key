"""
Activation repository for data access operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.activation import ActivationModel
from database.repository.base import BaseRepository
from core.constants import ActivationStatus


class ActivationRepository(BaseRepository[ActivationModel]):
    """Repository for activation data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ActivationModel)

    async def get_by_license_id(self, license_id: str) -> list[ActivationModel]:
        """Get all activations for a license."""
        return await self.get_all(filters={"license_id": license_id})

    async def get_by_customer_id(self, customer_id: str) -> list[ActivationModel]:
        """Get all activations for a customer."""
        return await self.get_all(filters={"customer_id": customer_id})

    async def get_by_machine_id(self, machine_id: str) -> list[ActivationModel]:
        """Get all activations for a machine."""
        return await self.get_all(filters={"machine_id": machine_id})

    async def get_active_activations(self) -> list[ActivationModel]:
        """Get all active activations."""
        return await self.get_all(filters={"status": ActivationStatus.ACTIVATED})

    async def get_offline_activations(self) -> list[ActivationModel]:
        """Get all offline activation requests."""
        return await self.get_all(filters={"activation_type": "offline"})