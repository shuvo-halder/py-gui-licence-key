"""
Audit log database model.

This module defines the AuditLog model for tracking all security-sensitive
operations, user actions, and system events for compliance and monitoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from core.constants import AuditAction


class AuditLogModel(Base):
    """ORM model for audit log entries."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Action information
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction),
        nullable=False,
        index=True,
    )
    action_description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # What was affected
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Details
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failure, warning
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Session
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        """String representation of the audit log entry."""
        return f"<AuditLogModel(action='{self.action}', user='{self.username}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "action": self.action.value,
            "action_description": self.action_description,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "user_ip": self.user_ip,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "details": self.details,
            "changes": self.changes,
            "status": self.status,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }