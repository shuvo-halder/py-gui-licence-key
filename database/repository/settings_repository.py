"""
Settings repository for data access operations.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.settings import AppSettingsModel
from database.repository.base import BaseRepository


class SettingsRepository(BaseRepository[AppSettingsModel]):
    """Repository for settings data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AppSettingsModel)

    async def get_by_key(self, key: str) -> Optional[AppSettingsModel]:
        """Get a setting by its key."""
        return await self.get_by_field("key", key)

    async def get_by_category(self, category: str) -> list[AppSettingsModel]:
        """Get all settings in a category."""
        return await self.get_all(filters={"category": category})

    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get the value of a setting by key."""
        setting = await self.get_by_key(key)
        if setting is None:
            return default
        return setting.value

    async def set_value(self, key: str, value: Any, category: str = "general") -> AppSettingsModel:
        """Set the value of a setting, creating it if it doesn't exist."""
        existing = await self.get_by_key(key)
        if existing:
            return await self.update(existing.id, value=value)
        return await self.create(key=key, value=value, category=category)

    async def get_system_settings(self) -> list[AppSettingsModel]:
        """Get all system settings."""
        return await self.get_all(filters={"is_system": True})

    async def get_encrypted_settings(self) -> list[AppSettingsModel]:
        """Get all encrypted settings."""
        return await self.get_all(filters={"is_encrypted": True})