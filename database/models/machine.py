"""
Machine database model.

This module defines the Machine model for managing registered machines,
their hardware fingerprints, and activation status.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from core.constants import MachineStatus


class MachineModel(Base):
    """ORM model for registered machines."""

    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Owner associations
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id"),
        nullable=False,
    )
    license_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("licenses.id"),
        nullable=False,
    )
    
    # Machine identification
    machine_name: Mapped[str] = mapped_column(String(255), nullable=False)
    machine_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Hardware details (encrypted in database)
    cpu_serial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    motherboard_serial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bios_serial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    disk_serial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    machine_guid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # System information
    os_info: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Status
    status: Mapped[MachineStatus] = mapped_column(
        SAEnum(MachineStatus),
        default=MachineStatus.ACTIVE,
    )
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklist_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Activation
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
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
    customer = relationship("CustomerModel", back_populates="machines", lazy="selectin")
    license = relationship("LicenseModel", back_populates="machines", lazy="selectin")
    activations = relationship("ActivationModel", back_populates="machine", lazy="selectin")

    def __repr__(self) -> str:
        """String representation of the machine."""
        return f"<MachineModel(name='{self.machine_name}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "license_id": self.license_id,
            "machine_name": self.machine_name,
            "machine_fingerprint": self.machine_fingerprint[:16] + "...",
            "os_info": self.os_info,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "status": self.status.value,
            "is_blacklisted": self.is_blacklisted,
            "blacklist_reason": self.blacklist_reason,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }