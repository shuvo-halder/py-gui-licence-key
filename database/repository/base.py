"""
Base repository class implementing the Repository Pattern.

This module provides a generic base repository with common CRUD operations
that all specific repositories inherit from. It uses SQLAlchemy async sessions
and provides type-safe operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from database import Base
from core.logger import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with common database operations.

    Provides CRUD operations, pagination, and filtering capabilities
    that can be inherited by specific entity repositories.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages.
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelType]) -> None:
        """
        Initialize the repository.

        Args:
            session: Async SQLAlchemy session.
            model_class: The model class this repository manages.
        """
        self.session = session
        self.model_class = model_class

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new entity.

        Args:
            **kwargs: Field values for the new entity.

        Returns:
            The created entity instance.
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        logger.debug(f"Created {self.model_class.__name__}: {instance.id}")
        return instance

    async def get(self, id: str) -> Optional[ModelType]:
        """
        Get an entity by its ID.

        Args:
            id: The entity's UUID.

        Returns:
            The entity if found, None otherwise.
        """
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_field(
        self, field: str, value: Any, unique: bool = True
    ) -> Optional[ModelType] | list[ModelType]:
        """
        Get entities by a specific field value.

        Args:
            field: The field name to filter by.
            value: The value to filter for.
            unique: If True, returns a single entity. If False, returns a list.

        Returns:
            Single entity or list of entities matching the filter.
        """
        column = getattr(self.model_class, field, None)
        if column is None:
            raise ValueError(f"Field '{field}' does not exist on {self.model_class.__name__}")

        query = select(self.model_class).where(column == value)
        result = await self.session.execute(query)

        if unique:
            return result.scalar_one_or_none()
        return list(result.scalars().all())

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> list[ModelType]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            order_by: Field name to order by.
            descending: If True, order in descending direction.

        Returns:
            List of entities.
        """
        query = select(self.model_class)

        if order_by:
            column = getattr(self.model_class, order_by, None)
            if column is not None:
                query = query.order_by(column.desc() if descending else column.asc())

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, id: str, **kwargs: Any) -> Optional[ModelType]:
        """
        Update an entity by its ID.

        Args:
            id: The entity's UUID.
            **kwargs: Field values to update.

        Returns:
            The updated entity if found, None otherwise.
        """
        # Remove None values to avoid overwriting with None
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            return await self.get(id)

        # Add updated timestamp
        if hasattr(self.model_class, "updated_at"):
            update_data["updated_at"] = datetime.utcnow()

        query = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**update_data)
            .returning(self.model_class)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        updated = result.scalar_one_or_none()

        if updated:
            logger.debug(f"Updated {self.model_class.__name__}: {id}")
        return updated

    async def delete(self, id: str, soft: bool = True) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id: The entity's UUID.
            soft: If True, performs a soft delete by setting is_deleted flag.

        Returns:
            True if deleted, False if not found.
        """
        if soft and hasattr(self.model_class, "is_deleted"):
            return await self.update(id, is_deleted=True) is not None

        query = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        await self.session.flush()
        deleted = result.rowcount > 0

        if deleted:
            logger.debug(f"Deleted {self.model_class.__name__}: {id}")
        return deleted

    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Count entities, optionally with filters.

        Args:
            filters: Optional dictionary of field-value pairs to filter by.

        Returns:
            The count of matching entities.
        """
        query = select(func.count()).select_from(self.model_class)

        if filters:
            for field, value in filters.items():
                column = getattr(self.model_class, field, None)
                if column is not None:
                    query = query.where(column == value)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists(self, **filters: Any) -> bool:
        """
        Check if an entity exists matching the given filters.

        Args:
            **filters: Field-value pairs to filter by.

        Returns:
            True if at least one matching entity exists.
        """
        query = select(self.model_class)
        for field, value in filters.items():
            column = getattr(self.model_class, field, None)
            if column is not None:
                query = query.where(column == value)

        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelType]:
        """
        Create multiple entities in bulk.

        Args:
            items: List of dictionaries with field values.

        Returns:
            List of created entities.
        """
        instances = [self.model_class(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        logger.debug(f"Bulk created {len(instances)} {self.model_class.__name__}")
        return instances

    async def search(
        self,
        search_term: str,
        fields: list[str],
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Search entities by text fields.

        Args:
            search_term: The text to search for.
            fields: List of field names to search in.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of matching entities.
        """
        query = select(self.model_class)
        conditions = []

        for field in fields:
            column = getattr(self.model_class, field, None)
            if column is not None:
                conditions.append(column.ilike(f"%{search_term}%"))

        if conditions:
            from sqlalchemy import or_
            query = query.where(or_(*conditions))

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())