"""
Audit log repository for data access operations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.audit_log import AuditLogModel
from database.repository.base import BaseRepository
from core.constants import AuditAction


class AuditLogRepository(BaseRepository[AuditLogModel]):
    """Repository for audit log data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLogModel)

    async def get_by_user(self, user_id: str) -> list[AuditLogModel]:
        """Get all audit logs for a specific user."""
        return await self.get_all(filters={"user_id": user_id})

    async def get_by_action(self, action: AuditAction) -> list[AuditLogModel]:
        """Get all audit logs for a specific action."""
        return await self.get_all(filters={"action": action})

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[AuditLogModel]:
        """Get audit logs within a date range."""
        query = select(AuditLogModel).where(
            and_(
                AuditLogModel.created_at >= start_date,
                AuditLogModel.created_at <= end_date,
            )
        ).order_by(AuditLogModel.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_logs(self, limit: int = 50) -> list[AuditLogModel]:
        """Get the most recent audit logs."""
        return await self.get_all(limit=limit, order_by="created_at", descending=True)

    async def get_errors(self) -> list[AuditLogModel]:
        """Get all error audit logs."""
        return await self.get_all(filters={"status": "failure"})

    async def get_by_resource(self, resource_type: str, resource_id: str) -> list[AuditLogModel]:
        """Get audit logs for a specific resource."""
        return await self.get_all(
            filters={
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )

    async def get_logs_today(self) -> list[AuditLogModel]:
        """Get all audit logs from today."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return await self.get_by_date_range(today, tomorrow)