"""
Repository module initialization.

This module exports all repository classes for data access operations.
"""

from database.repository.base import BaseRepository
from database.repository.product_repository import ProductRepository
from database.repository.customer_repository import CustomerRepository
from database.repository.license_repository import LicenseRepository
from database.repository.subscription_repository import SubscriptionRepository
from database.repository.machine_repository import MachineRepository
from database.repository.activation_repository import ActivationRepository
from database.repository.audit_log_repository import AuditLogRepository
from database.repository.settings_repository import SettingsRepository
from database.repository.software_product_repository import SoftwareProductRepository

__all__ = [
    "BaseRepository",
    "ProductRepository",
    "CustomerRepository",
    "LicenseRepository",
    "SubscriptionRepository",
    "MachineRepository",
    "ActivationRepository",
    "AuditLogRepository",
    "SettingsRepository",
    "SoftwareProductRepository",
]
