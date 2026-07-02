"""
Subscription database model.

This module defines the Subscription model for managing recurring subscriptions,
their intervals, status, and renewal tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, Float, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.constants import SubscriptionStatus, SubscriptionInterval


class SubscriptionModel(Base):
    """ORM model for subscriptions."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # License association
    license_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("licenses.id"),
        nullable=False,
        unique=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id"),
        nullable=False,
    )
    
    # Subscription details
    interval: Mapped[SubscriptionInterval] = mapped_column(
        SAEnum(SubscriptionInterval),
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
    )
    
    # Billing
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Dates
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    grace_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Renewal
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    renewal_count: Mapped[int] = mapped_column(default=0)
    last_renewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_billing_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Payment
    payment_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    license = relationship("LicenseModel", back_populates="subscription", lazy="selectin")
    product = relationship("ProductModel", back_populates="subscriptions", lazy="selectin")
    customer = relationship("CustomerModel", back_populates="subscriptions", lazy="selectin")

    def __repr__(self) -> str:
        """String representation of the subscription."""
        return f"<SubscriptionModel(interval='{self.interval}', status='{self.status}')>"

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return True

    def is_in_grace_period(self) -> bool:
        """Check if subscription is in grace period."""
        if self.grace_period_end and datetime.utcnow() <= self.grace_period_end:
            return True
        return False

    def days_until_expiry(self) -> int:
        """Get days until subscription expires."""
        if not self.end_date:
            return -1
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "license_id": self.license_id,
            "product_id": self.product_id,
            "customer_id": self.customer_id,
            "interval": self.interval.value,
            "status": self.status.value,
            "amount": self.amount,
            "currency": self.currency,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "grace_period_end": self.grace_period_end.isoformat() if self.grace_period_end else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "auto_renew": self.auto_renew,
            "renewal_count": self.renewal_count,
            "last_renewed_at": self.last_renewed_at.isoformat() if self.last_renewed_at else None,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }