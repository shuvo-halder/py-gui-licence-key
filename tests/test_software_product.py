"""
Unit tests for the Software Product module.

Tests cover the database model, repository, service layer,
and client SDK generation.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime
from typing import AsyncGenerator, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from database.models.software_product import SoftwareProductModel
from database.repository.software_product_repository import SoftwareProductRepository
from services.software_product.service import SoftwareProductService
from services.encryption.service import EncryptionService


# --- Fixtures ---

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def repository(db_session: AsyncSession) -> SoftwareProductRepository:
    """Create a SoftwareProductRepository instance."""
    return SoftwareProductRepository(db_session)


@pytest_asyncio.fixture
async def service(db_session: AsyncSession) -> SoftwareProductService:
    """Create a SoftwareProductService instance with mock encryption."""
    encryption = MagicMock(spec=EncryptionService)
    encryption.get_public_key_pem.return_value = "mock-public-key-pem"
    encryption.sign_data.return_value = "mock-signature"
    return SoftwareProductService(db_session, encryption)


# --- Model Tests ---

class TestSoftwareProductModel:
    """Tests for SoftwareProductModel."""

    def test_create_model(self) -> None:
        """Test creating a SoftwareProductModel instance."""
        product = SoftwareProductModel(
            name="Test App",
            version="1.0.0",
            validation_type="online",
            machine_lock=True,
            max_activations=5,
            anti_tamper=True,
            clock_protection=True,
            is_active=True,
            is_deleted=False,
        )
        assert product.name == "Test App"
        assert product.version == "1.0.0"
        assert product.validation_type == "online"
        assert product.machine_lock is True
        assert product.max_activations == 5
        assert product.anti_tamper is True
        assert product.clock_protection is True
        assert product.is_active is True
        assert product.is_deleted is False

    def test_model_to_dict(self) -> None:
        """Test converting model to dictionary."""
        product = SoftwareProductModel(
            name="Test App",
            version="2.0.0",
            validation_type="offline",
            machine_lock=False,
            max_activations=10,
            anti_tamper=False,
            clock_protection=False,
            feature_flags='["reporting", "export"]',
        )
        data = product.to_dict()
        assert data["name"] == "Test App"
        assert data["version"] == "2.0.0"
        assert data["validation_type"] == "offline"
        assert data["machine_lock"] is False
        assert data["max_activations"] == 10
        assert data["anti_tamper"] is False
        assert data["clock_protection"] is False
        assert data["feature_flags"] == '["reporting", "export"]'

    def test_model_repr(self) -> None:
        """Test string representation."""
        product = SoftwareProductModel(
            name="MyApp",
            version="3.0.0",
            app_id="test-uuid-1234",
        )
        repr_str = repr(product)
        assert "MyApp" in repr_str
        assert "3.0.0" in repr_str
        assert "test-uuid-1234" in repr_str


# --- Repository Tests ---

@pytest.mark.asyncio
class TestSoftwareProductRepository:
    """Tests for SoftwareProductRepository."""

    async def test_create_product(
        self, repository: SoftwareProductRepository, db_session: AsyncSession
    ) -> None:
        """Test creating a software product."""
        product = await repository.create(
            app_id=str(uuid.uuid4()),
            name="Test Product",
            version="1.0.0",
            validation_type="online",
        )
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.version == "1.0.0"

    async def test_get_by_app_id(
        self, repository: SoftwareProductRepository, db_session: AsyncSession
    ) -> None:
        """Test retrieving a product by app_id."""
        app_id = str(uuid.uuid4())
        await repository.create(
            app_id=app_id,
            name="App ID Test",
            version="1.0.0",
        )
        product = await repository.get_by_app_id(app_id)
        assert product is not None
        assert product.name == "App ID Test"

    async def test_get_by_name(
        self, repository: SoftwareProductRepository, db_session: AsyncSession
    ) -> None:
        """Test retrieving a product by name."""
        await repository.create(
            app_id=str(uuid.uuid4()),
            name="Unique Name",
            version="1.0.0",
        )
        product = await repository.get_by_name("Unique Name")
        assert product is not None
        assert product.name == "Unique Name"

    async def test_search_products(
        self, repository: SoftwareProductRepository, db_session: AsyncSession
    ) -> None:
        """Test searching products."""
        await repository.create(
            app_id=str(uuid.uuid4()),
            name="Alpha App",
            version="1.0.0",
            company_name="Alpha Corp",
        )
        await repository.create(
            app_id=str(uuid.uuid4()),
            name="Beta App",
            version="2.0.0",
            company_name="Beta Inc",
        )

        results = await repository.search_products("Alpha")
        assert len(results) == 1
        assert results[0].name == "Alpha App"

        results = await repository.search_products("App")
        assert len(results) == 2

    async def test_get_active_products(
        self, repository: SoftwareProductRepository, db_session: AsyncSession
    ) -> None:
        """Test getting active products."""
        await repository.create(
            app_id=str(uuid.uuid4()),
            name="Active Product",
            version="1.0.0",
            is_active=True,
        )
        await repository.create(
            app_id=str(uuid.uuid4()),
            name="Inactive Product",
            version="1.0.0",
            is_active=False,
        )

        products = await repository.get_active_products()
        names = [p.name for p in products]
        assert "Active Product" in names
        assert "Inactive Product" in names  # is_deleted=False, not is_active filter


# --- Service Tests ---

@pytest.mark.asyncio
class TestSoftwareProductService:
    """Tests for SoftwareProductService."""

    async def test_create_product(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test creating a product through the service."""
        product = await service.create_product(
            name="Service Test",
            version="1.0.0",
            validation_type="hybrid",
            company_name="Test Corp",
            machine_lock=True,
            max_activations=3,
            anti_tamper=True,
            clock_protection=True,
        )
        assert product.name == "Service Test"
        assert product.validation_type == "hybrid"
        assert product.company_name == "Test Corp"
        assert product.max_activations == 3

    async def test_create_duplicate_product(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test that creating a duplicate product raises ValueError."""
        await service.create_product(name="Duplicate", version="1.0.0")
        with pytest.raises(ValueError, match="already exists"):
            await service.create_product(name="Duplicate", version="2.0.0")

    async def test_get_product(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test getting a product by ID."""
        created = await service.create_product(
            name="Get Test", version="1.0.0"
        )
        retrieved = await service.get_product(created.id)
        assert retrieved is not None
        assert retrieved.name == "Get Test"

    async def test_get_product_by_app_id(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test getting a product by app_id."""
        created = await service.create_product(
            name="AppID Test", version="1.0.0"
        )
        retrieved = await service.get_product_by_app_id(created.app_id)
        assert retrieved is not None
        assert retrieved.name == "AppID Test"

    async def test_update_product(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test updating a product."""
        created = await service.create_product(
            name="Update Test", version="1.0.0"
        )
        updated = await service.update_product(
            created.id, name="Updated Name", version="2.0.0"
        )
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.version == "2.0.0"

    async def test_delete_product(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test soft-deleting a product."""
        created = await service.create_product(
            name="Delete Test", version="1.0.0"
        )
        result = await service.delete_product(created.id)
        assert result is True

        # Verify soft delete
        deleted = await service.get_product(created.id)
        assert deleted is not None
        assert deleted.is_deleted is True

    async def test_list_products(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test listing products."""
        await service.create_product(name="List A", version="1.0.0")
        await service.create_product(name="List B", version="2.0.0")
        products = await service.list_products()
        assert len(products) == 2

    async def test_search_products(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test searching products through service."""
        await service.create_product(
            name="Searchable App", version="1.0.0",
            company_name="Search Corp",
        )
        results = await service.search_products("Searchable")
        assert len(results) == 1
        assert results[0].name == "Searchable App"

    async def test_count_products(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test counting products."""
        await service.create_product(name="Count A", version="1.0.0")
        await service.create_product(name="Count B", version="2.0.0")
        count = await service.count_products()
        assert count == 2

    async def test_generate_client_sdk(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test generating a client SDK package."""
        product = await service.create_product(
            name="SDK Test",
            version="1.0.0",
            validation_type="online",
            company_name="SDK Corp",
            anti_tamper=True,
            clock_protection=True,
            machine_lock=True,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = await service.generate_client_sdk(
                product.id, output_dir=tmpdir
            )
            assert zip_path is not None
            assert zip_path.endswith(".zip")
            assert os.path.exists(zip_path)

    async def test_generate_sdk_nonexistent_product(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test SDK generation for non-existent product raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await service.generate_client_sdk("non-existent-id")

    async def test_to_dict(
        self, service: SoftwareProductService, db_session: AsyncSession
    ) -> None:
        """Test converting product to dictionary."""
        product = await service.create_product(
            name="Dict Test", version="1.0.0"
        )
        data = await service.to_dict(product)
        assert data["name"] == "Dict Test"
        assert data["version"] == "1.0.0"
        assert "id" in data
        assert "app_id" in data
        assert "created_at" in data
        assert "updated_at" in data