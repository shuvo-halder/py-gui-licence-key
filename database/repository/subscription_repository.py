"""
Subscription repository for data access operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.subscription import SubscriptionModel
from database.repository.base import BaseRepository
from core.constants import SubscriptionStatus, SubscriptionInterval


class SubscriptionRepository(BaseRepository[SubscriptionModel]):
    """Repository for subscription data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SubscriptionModel)

    async def get_by_license_id(self, license_id: str) -> Optional[SubscriptionModel]:
        """Get subscription by license ID."""
        return await self.get_by_field("license_id", license_id)

    async def get_active_subscriptions(self) -> list[SubscriptionModel]:
        """Get all active subscriptions."""
        return await self.get_all(filters={"status": SubscriptionStatus.ACTIVE})

    async def get_expired_subscriptions(self) -> list[SubscriptionModel]:
        """Get all expired subscriptions."""
        return await self.get_all(filters={"status": SubscriptionStatus.EXPIRED})

    async def get_subscriptions_by_customer(self, customer_id: str) -> list[SubscriptionModel]:
        """Get all subscriptions for a customer."""
        return await self.get_all(filters={"customer_id": customer_id})

    async def get_subscriptions_by_interval(self, interval: SubscriptionInterval) -> list[SubscriptionModel]:
        """Get all subscriptions with a specific interval."""
        return await self.get_all(filters={"interval": interval})

    async def get_subscriptions_due_for_renewal(self) -> list[SubscriptionModel]:
        """Get subscriptions that need renewal."""
        query = select(SubscriptionModel).where(
            and_(
                SubscriptionModel.status == SubscriptionStatus.ACTIVE,
                SubscriptionModel.auto_renew == True,
                SubscriptionModel.next_billing_date <= datetime.utcnow(),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_subscriptions_in_grace_period(self) -> list[SubscriptionModel]:
        """Get subscriptions currently in grace period."""
        query = select(SubscriptionModel).where(
            and_(
                SubscriptionModel.status == SubscriptionStatus.GRACE_PERIOD,
                SubscriptionModel.grace_period_end >= datetime.utcnow(),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())