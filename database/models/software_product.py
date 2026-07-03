"""
SoftwareProduct database model.

This module defines the SoftwareProduct model for managing registered
software applications that can be licensed through the system.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SoftwareProductModel(Base):
    """ORM model for registered software products."""

    __tablename__ = "software_products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    app_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    exe_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    validation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="online",
    )
    machine_lock: Mapped[bool] = mapped_column(Boolean, default=True)
    max_activations: Mapped[int] = mapped_column(Integer, default=5)
    anti_tamper: Mapped[bool] = mapped_column(Boolean, default=True)
    clock_protection: Mapped[bool] = mapped_column(Boolean, default=True)
    feature_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    def __repr__(self) -> str:
        """String representation of the software product."""
        return (
            f"<SoftwareProductModel(name='{self.name}', "
            f"version='{self.version}', "
            f"app_id='{self.app_id}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "name": self.name,
            "version": self.version,
            "exe_name": self.exe_name,
            "company_name": self.company_name,
            "validation_type": self.validation_type,
            "machine_lock": self.machine_lock,
            "max_activations": self.max_activations,
            "anti_tamper": self.anti_tamper,
            "clock_protection": self.clock_protection,
            "feature_flags": self.feature_flags,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }