"""
Database models initialization.

This module exports all SQLAlchemy ORM models for easy importing.
"""

from database.models.product import ProductModel
from database.models.customer import CustomerModel
from database.models.license import LicenseModel
from database.models.subscription import SubscriptionModel
from database.models.machine import MachineModel
from database.models.activation import ActivationModel
from database.models.audit_log import AuditLogModel
from database.models.settings import AppSettingsModel
from database.models.software_product import SoftwareProductModel

__all__ = [
    "ProductModel",
    "CustomerModel",
    "LicenseModel",
    "SubscriptionModel",
    "MachineModel",
    "ActivationModel",
    "AuditLogModel",
    "AppSettingsModel",
    "SoftwareProductModel",
]
