"""
Customer repository for data access operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.customer import CustomerModel
from database.repository.base import BaseRepository


class CustomerRepository(BaseRepository[CustomerModel]):
    """Repository for customer data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CustomerModel)

    async def get_by_email(self, email: str) -> Optional[CustomerModel]:
        """Get a customer by email."""
        return await self.get_by_field("email", email)

    async def get_active_customers(self) -> list[CustomerModel]:
        """Get all active customers."""
        return await self.get_all(filters={"is_active": True})