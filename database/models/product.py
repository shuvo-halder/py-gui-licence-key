"""
Product database model.

This module defines the Product model for managing software products
with their versions, modules, and licensing policies.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class ProductModel(Base):
    """ORM model for software products."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Licensing configuration
    allow_trial: Mapped[bool] = mapped_column(Boolean, default=True)
    trial_days: Mapped[int] = mapped_column(default=30)
    max_machines: Mapped[int] = mapped_column(default=5)
    allow_offline_activation: Mapped[bool] = mapped_column(Boolean, default=True)
    require_online_validation: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Features/modules available for this product
    available_features: Mapped[dict] = mapped_column(JSON, default=list)
    
    # Pricing
    price_monthly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_lifetime: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_enterprise: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    licenses = relationship("LicenseModel", back_populates="product", lazy="selectin")
    subscriptions = relationship("SubscriptionModel", back_populates="product", lazy="selectin")

    def __repr__(self) -> str:
        """String representation of the product."""
        return f"<ProductModel(name='{self.name}', version='{self.version}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "publisher": self.publisher,
            "website": self.website,
            "support_email": self.support_email,
            "allow_trial": self.allow_trial,
            "trial_days": self.trial_days,
            "max_machines": self.max_machines,
            "allow_offline_activation": self.allow_offline_activation,
            "require_online_validation": self.require_online_validation,
            "available_features": self.available_features,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "price_lifetime": self.price_lifetime,
            "price_enterprise": self.price_enterprise,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }