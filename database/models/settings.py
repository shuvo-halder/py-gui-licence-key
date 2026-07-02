"""
Application settings database model.

This module defines the AppSettings model for persisting application
configuration, user preferences, and encryption keys.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class AppSettingsModel(Base):
    """ORM model for application settings."""

    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Setting identification
    key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
        index=True,
    )
    
    # Setting value (stored as JSON for flexibility)
    value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    value_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="string",
    )  # string, integer, boolean, json, encrypted
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Validation
    validation_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
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
        """String representation of the settings entry."""
        return f"<AppSettingsModel(key='{self.key}', category='{self.category}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "category": self.category,
            "value": self.value,
            "value_type": self.value_type,
            "description": self.description,
            "is_encrypted": self.is_encrypted,
            "is_system": self.is_system,
            "is_required": self.is_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }