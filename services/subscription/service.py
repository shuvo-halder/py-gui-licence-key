"""
Subscription management service.

Handles subscription lifecycle including creation, renewal, cancellation,
grace period management, and status tracking.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import (
    Constants,
    SubscriptionStatus,
    SubscriptionInterval,
)
from core.logger import get_logger
from database.repository.subscription_repository import SubscriptionRepository
from database.repository.license_repository import LicenseRepository
from database.repository.customer_repository import CustomerRepository
from database.repository.product_repository import ProductRepository

logger = get_logger(__name__)


class SubscriptionService:
    """
    Service for managing subscription lifecycles.

    Supports monthly, quarterly, yearly, lifetime, and enterprise subscriptions
    with automatic renewal tracking and grace period management.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the subscription service.

        Args:
            session: Database session.
        """
        self.session = session
        self.subscription_repo = SubscriptionRepository(session)
        self.license_repo = LicenseRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.product_repo = ProductRepository(session)

    async def create_subscription(
        self,
        license_id: str,
        customer_id: str,
        product_id: str,
        interval: SubscriptionInterval,
        amount: Optional[float] = None,
        currency: str = "USD",
        auto_renew: bool = True,
        duration_days: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Create a new subscription for a license.

        Args:
            license_id: UUID of the license.
            customer_id: UUID of the customer.
            product_id: UUID of the product.
            interval: Billing interval.
            amount: Subscription price.
            currency: Currency code (default: USD).
            auto_renew: Whether to auto-renew.
            duration_days: Custom duration in days.

        Returns:
            Dictionary with created subscription data.
        """
        now = datetime.utcnow()

        # Calculate end date based on interval
        if duration_days:
            end_date = now + timedelta(days=duration_days)
        elif interval == SubscriptionInterval.MONTHLY:
            end_date = now + timedelta(days=30)
        elif interval == SubscriptionInterval.QUARTERLY:
            end_date = now + timedelta(days=90)
        elif interval == SubscriptionInterval.YEARLY:
            end_date = now + timedelta(days=365)
        elif interval == SubscriptionInterval.LIFETIME:
            end_date = None
        elif interval == SubscriptionInterval.ENTERPRISE:
            end_date = now + timedelta(days=365 * 5)
        else:
            end_date = now + timedelta(days=30)

        # Calculate grace period end
        grace_end = end_date + timedelta(days=Constants.GRACE_PERIOD_DAYS) if end_date else None

        # Calculate next billing date
        next_billing = end_date if auto_renew and end_date else None

        # Create subscription
        subscription = await self.subscription_repo.create(
            license_id=license_id,
            product_id=product_id,
            customer_id=customer_id,
            interval=interval,
            status=SubscriptionStatus.ACTIVE,
            amount=amount,
            currency=currency,
            start_date=now,
            end_date=end_date,
            grace_period_end=grace_end,
            auto_renew=auto_renew,
            renewal_count=0,
            next_billing_date=next_billing,
        )

        logger.info(
            "Subscription created: {interval} for license {license}",
            interval=interval.value,
            license=license_id[:8] + "...",
        )

        return subscription.to_dict()

    async def renew_subscription(
        self, license_id: str, payment_reference: str = ""
    ) -> dict[str, Any]:
        """
        Renew a subscription.

        Args:
            license_id: UUID of the license to renew.
            payment_reference: Payment transaction reference.

        Returns:
            Dictionary with renewed subscription data.
        """
        subscription = await self.subscription_repo.get_by_license_id(license_id)
        if not subscription:
            raise ValueError("No subscription found for this license")

        now = datetime.utcnow()

        # Calculate new end date
        if subscription.interval == SubscriptionInterval.MONTHLY:
            new_end = now + timedelta(days=30)
        elif subscription.interval == SubscriptionInterval.QUARTERLY:
            new_end = now + timedelta(days=90)
        elif subscription.interval == SubscriptionInterval.YEARLY:
            new_end = now + timedelta(days=365)
        else:
            new_end = now + timedelta(days=30)

        # Update subscription
        updated = await self.subscription_repo.update(
            subscription.id,
            status=SubscriptionStatus.ACTIVE,
            end_date=new_end,
            grace_period_end=new_end + timedelta(days=Constants.GRACE_PERIOD_DAYS),
            renewal_count=subscription.renewal_count + 1,
            last_renewed_at=now,
            next_billing_date=new_end if subscription.auto_renew else None,
            payment_reference=payment_reference or subscription.payment_reference,
        )

        logger.info(
            "Subscription renewed: {id} (renewal #{count})",
            id=subscription.id[:8] + "...",
            count=subscription.renewal_count + 1,
        )

        return updated.to_dict() if updated else {}

    async def cancel_subscription(
        self, license_id: str, reason: str = ""
    ) -> dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            license_id: UUID of the license.
            reason: Reason for cancellation.

        Returns:
            Dictionary with updated subscription data.
        """
        subscription = await self.subscription_repo.get_by_license_id(license_id)
        if not subscription:
            raise ValueError("No subscription found for this license")

        updated = await self.subscription_repo.update(
            subscription.id,
            status=SubscriptionStatus.CANCELLED,
            cancelled_at=datetime.utcnow(),
            auto_renew=False,
        )

        logger.info(
            "Subscription cancelled: {id} - {reason}",
            id=subscription.id[:8] + "...",
            reason=reason or "No reason provided",
        )

        return updated.to_dict() if updated else {}

    async def suspend_subscription(
        self, license_id: str, reason: str = ""
    ) -> dict[str, Any]:
        """
        Suspend a subscription.

        Args:
            license_id: UUID of the license.
            reason: Reason for suspension.

        Returns:
            Dictionary with updated subscription data.
        """
        subscription = await self.subscription_repo.get_by_license_id(license_id)
        if not subscription:
            raise ValueError("No subscription found for this license")

        updated = await self.subscription_repo.update(
            subscription.id,
            status=SubscriptionStatus.SUSPENDED,
        )

        logger.warning(
            "Subscription suspended: {id} - {reason}",
            id=subscription.id[:8] + "...",
            reason=reason or "No reason provided",
        )

        return updated.to_dict() if updated else {}

    async def update_subscription_status(
        self, license_id: str, status: SubscriptionStatus
    ) -> dict[str, Any]:
        """
        Update subscription status manually.

        Args:
            license_id: UUID of the license.
            status: New subscription status.

        Returns:
            Dictionary with updated subscription data.
        """
        subscription = await self.subscription_repo.get_by_license_id(license_id)
        if not subscription:
            raise ValueError("No subscription found for this license")

        updated = await self.subscription_repo.update(
            subscription.id,
            status=status,
        )

        logger.info(
            "Subscription status updated: {id} -> {status}",
            id=subscription.id[:8] + "...",
            status=status.value,
        )

        return updated.to_dict() if updated else {}

    async def get_subscription(self, license_id: str) -> Optional[dict[str, Any]]:
        """
        Get subscription details for a license.

        Args:
            license_id: UUID of the license.

        Returns:
            Dictionary with subscription data or None.
        """
        subscription = await self.subscription_repo.get_by_license_id(license_id)
        return subscription.to_dict() if subscription else None

    async def get_expiring_subscriptions(
        self, days_threshold: int = 7
    ) -> list[dict[str, Any]]:
        """
        Get subscriptions that will expire within the specified days.

        Args:
            days_threshold: Number of days to check for expiry.

        Returns:
            List of expiring subscription dictionaries.
        """
        threshold = datetime.utcnow() + timedelta(days=days_threshold)
        subscriptions = await self.subscription_repo.get_active_subscriptions()

        expiring = []
        for sub in subscriptions:
            if sub.end_date and sub.end_date <= threshold:
                expiring.append(sub.to_dict())

        return expiring

    async def process_auto_renewals(self) -> list[dict[str, Any]]:
        """
        Process all subscriptions due for auto-renewal.

        Returns:
            List of renewed subscription dictionaries.
        """
        due = await self.subscription_repo.get_subscriptions_due_for_renewal()
        renewed = []

        for subscription in due:
            try:
                result = await self.renew_subscription(
                    subscription.license_id,
                    payment_reference=f"auto-renew-{datetime.utcnow().isoformat()}",
                )
                renewed.append(result)
            except Exception as e:
                logger.error(
                    "Auto-renewal failed for subscription {id}: {error}",
                    id=subscription.id[:8] + "...",
                    error=str(e),
                )

        return renewed

    async def get_subscription_statistics(self) -> dict[str, Any]:
        """
        Get subscription statistics for dashboard.

        Returns:
            Dictionary of subscription statistics.
        """
        total = await self.subscription_repo.count()
        active = await self.subscription_repo.count(
            {"status": SubscriptionStatus.ACTIVE}
        )
        expired = await self.subscription_repo.count(
            {"status": SubscriptionStatus.EXPIRED}
        )
        cancelled = await self.subscription_repo.count(
            {"status": SubscriptionStatus.CANCELLED}
        )
        suspended = await self.subscription_repo.count(
            {"status": SubscriptionStatus.SUSPENDED}
        )
        grace = await self.subscription_repo.count(
            {"status": SubscriptionStatus.GRACE_PERIOD}
        )

        return {
            "total": total,
            "active": active,
            "expired": expired,
            "cancelled": cancelled,
            "suspended": suspended,
            "grace_period": grace,
        }