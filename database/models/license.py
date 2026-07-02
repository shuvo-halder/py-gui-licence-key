"""
License database model.

This module defines the License model for managing license keys, their types,
expiration, features, and cryptographic signatures.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.constants import LicenseType, ActivationStatus


class LicenseModel(Base):
    """ORM model for software licenses."""

    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    license_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    license_type: Mapped[LicenseType] = mapped_column(
        SAEnum(LicenseType),
        nullable=False,
    )
    
    # Product and customer associations
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
    
    # License details
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Expiration
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_perpetual: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Features
    enabled_features: Mapped[dict] = mapped_column(JSON, default=list)
    max_machines: Mapped[int] = mapped_column(default=5)
    
    # Cryptographic data
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[ActivationStatus] = mapped_column(
        SAEnum(ActivationStatus),
        default=ActivationStatus.PENDING,
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
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
    product = relationship("ProductModel", back_populates="licenses", lazy="selectin")
    customer = relationship("CustomerModel", back_populates="licenses", lazy="selectin")
    activations = relationship("ActivationModel", back_populates="license", lazy="selectin")
    machines = relationship("MachineModel", back_populates="license", lazy="selectin")
    subscription = relationship("SubscriptionModel", back_populates="license", uselist=False, lazy="selectin")

    def __repr__(self) -> str:
        """String representation of the license."""
        return f"<LicenseModel(key='{self.license_key[:8]}...', type='{self.license_type}')>"

    def is_expired(self) -> bool:
        """Check if the license has expired."""
        if self.is_perpetual:
            return False
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "license_key": self.license_key,
            "license_type": self.license_type.value,
            "product_id": self.product_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "product_name": self.product_name,
            "product_version": self.product_version,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_perpetual": self.is_perpetual,
            "enabled_features": self.enabled_features,
            "max_machines": self.max_machines,
            "signature": self.signature,
            "status": self.status.value,
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }