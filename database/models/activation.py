"""
Activation database model.

This module defines the Activation model for tracking license activation events,
both online and offline, along with their metadata and validation results.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.constants import ActivationStatus, ValidationResult


class ActivationModel(Base):
    """ORM model for license activations."""

    __tablename__ = "activations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Associations
    license_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("licenses.id"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id"),
        nullable=False,
    )
    machine_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("machines.id"),
        nullable=True,
    )
    
    # Activation details
    activation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="online",
    )  # "online" or "offline"
    status: Mapped[ActivationStatus] = mapped_column(
        SAEnum(ActivationStatus),
        default=ActivationStatus.PENDING,
    )
    validation_result: Mapped[Optional[ValidationResult]] = mapped_column(
        SAEnum(ValidationResult),
        nullable=True,
    )
    
    # Request/Response data
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    activation_code: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Machine info at activation time
    machine_fingerprint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    machine_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timing
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validation_count: Mapped[int] = mapped_column(default=0)
    
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
    license = relationship("LicenseModel", back_populates="activations", lazy="selectin")
    customer = relationship("CustomerModel", back_populates="activations", lazy="selectin")
    machine = relationship("MachineModel", back_populates="activations", lazy="selectin")

    def __repr__(self) -> str:
        """String representation of the activation."""
        return f"<ActivationModel(type='{self.activation_type}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "license_id": self.license_id,
            "customer_id": self.customer_id,
            "machine_id": self.machine_id,
            "activation_type": self.activation_type,
            "status": self.status.value,
            "validation_result": self.validation_result.value if self.validation_result else None,
            "machine_fingerprint": self.machine_fingerprint[:16] + "..." if self.machine_fingerprint else None,
            "machine_name": self.machine_name,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
            "last_validated_at": self.last_validated_at.isoformat() if self.last_validated_at else None,
            "validation_count": self.validation_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }