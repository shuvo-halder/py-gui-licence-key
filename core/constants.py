"""
Application constants and enumerations.

This module defines all constant values, enumerations, and type definitions
used throughout the application. Centralizing constants ensures consistency
and makes maintenance easier.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Final


class LicenseType(str, Enum):
    """Types of licenses that can be generated."""

    TRIAL = "trial"
    LIFETIME = "lifetime"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Possible states of a subscription."""

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    GRACE_PERIOD = "grace_period"


class SubscriptionInterval(str, Enum):
    """Subscription billing intervals."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"
    ENTERPRISE = "enterprise"


class ActivationStatus(str, Enum):
    """Possible states of license activation."""

    PENDING = "pending"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    REVOKED = "revoked"
    BLACKLISTED = "blacklisted"


class MachineStatus(str, Enum):
    """Possible states of a registered machine."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"
    REPLACED = "replaced"


class ValidationResult(str, Enum):
    """Results of license validation."""

    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    TAMPERED = "tampered"
    MACHINE_MISMATCH = "machine_mismatch"
    CLOCK_MANIPULATED = "clock_manipulated"
    SUBSCRIPTION_EXPIRED = "subscription_expired"


class AuditAction(str, Enum):
    """Types of audit log actions."""

    LOGIN = "login"
    LOGOUT = "logout"
    ACTIVATION = "activation"
    DEACTIVATION = "deactivation"
    VALIDATION = "validation"
    RENEWAL = "renewal"
    REVOCATION = "revocation"
    LICENSE_GENERATED = "license_generated"
    MACHINE_REGISTERED = "machine_registered"
    MACHINE_REMOVED = "machine_removed"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SETTINGS_CHANGED = "settings_changed"
    ERROR = "error"
    TAMPERING_DETECTED = "tampering_detected"


class EventType(str, Enum):
    """Types of events for notifications."""

    LICENSE_EXPIRING = "license_expiring"
    SUBSCRIPTION_ENDING = "subscription_ending"
    ACTIVATION_FAILED = "activation_failed"
    SERVER_OFFLINE = "server_offline"
    UPDATE_AVAILABLE = "update_available"
    TAMPERING_DETECTED = "tampering_detected"


class Feature(str, Enum):
    """Available software features that can be licensed."""

    REPORTING = "reporting"
    AI_MODULE = "ai_module"
    EXPORT = "export"
    API_ACCESS = "api_access"
    CLOUD_SYNC = "cloud_sync"
    BACKUP = "backup"
    PREMIUM_DASHBOARD = "premium_dashboard"
    MULTI_USER = "multi_user"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_INTEGRATION = "custom_integration"


@dataclass(frozen=True)
class Constants:
    """
    Application-wide constants.

    This class contains all constant values used across the application.
    Using a frozen dataclass ensures immutability.
    """

    # Application
    APP_NAME: Final[str] = "Software License Manager"
    APP_VERSION: Final[str] = "1.0.0"
    COMPANY_NAME: Final[str] = "LicenseManager Inc."
    COPYRIGHT: Final[str] = "Copyright 2024 LicenseManager Inc. All rights reserved."

    # License
    MAX_MACHINES_PER_LICENSE: Final[int] = 5
    TRIAL_DAYS: Final[int] = 30
    GRACE_PERIOD_DAYS: Final[int] = 7
    LICENSE_KEY_LENGTH: Final[int] = 32
    LICENSE_KEY_SEGMENTS: Final[int] = 4
    LICENSE_KEY_SEGMENT_LENGTH: Final[int] = 8

    # Security
    SALT_LENGTH: Final[int] = 32
    IV_LENGTH: Final[int] = 16
    HASH_ITERATIONS: Final[int] = 100000
    MIN_PASSWORD_LENGTH: Final[int] = 8
    SESSION_TIMEOUT_MINUTES: Final[int] = 30

    # API
    API_VERSION: Final[str] = "v1"
    API_PREFIX: Final[str] = f"/api/{API_VERSION}"
    MAX_UPLOAD_SIZE_MB: Final[int] = 10
    REQUEST_TIMEOUT_SECONDS: Final[int] = 30

    # Database
    DEFAULT_PAGE_SIZE: Final[int] = 20
    MAX_PAGE_SIZE: Final[int] = 100

    # File extensions
    LICENSE_FILE_EXTENSION: Final[str] = ".lic"
    REQUEST_FILE_EXTENSION: Final[str] = ".request"
    BACKUP_FILE_EXTENSION: Final[str] = ".backup"
    EXPORT_FILE_EXTENSION: Final[str] = ".csv"

    # UI
    WINDOW_MIN_WIDTH: Final[int] = 1024
    WINDOW_MIN_HEIGHT: Final[int] = 768
    WINDOW_DEFAULT_WIDTH: Final[int] = 1280
    WINDOW_DEFAULT_HEIGHT: Final[int] = 800
    ANIMATION_DURATION: Final[int] = 300
    TOAST_DURATION: Final[int] = 5000

    # Paths
    CONFIG_DIR_NAME: Final[str] = ".licensemanager"
    KEYS_DIR_NAME: Final[str] = "keys"
    DATA_DIR_NAME: Final[str] = "data"
    LOGS_DIR_NAME: Final[str] = "logs"
    LICENSES_DIR_NAME: Final[str] = "licenses"
    BACKUPS_DIR_NAME: Final[str] = "backups"
    EXPORTS_DIR_NAME: Final[str] = "exports"

    # Encryption
    RSA_PUBLIC_KEY_FILE: Final[str] = "public_key.pem"
    RSA_PRIVATE_KEY_FILE: Final[str] = "private_key.pem"
    AES_KEY_FILE: Final[str] = "aes_key.key"

    # Error messages
    ERROR_INVALID_LICENSE: Final[str] = "Invalid license key"
    ERROR_EXPIRED_LICENSE: Final[str] = "License has expired"
    ERROR_REVOKED_LICENSE: Final[str] = "License has been revoked"
    ERROR_MACHINE_MISMATCH: Final[str] = "Machine fingerprint does not match"
    ERROR_CLOCK_MANIPULATION: Final[str] = "System clock manipulation detected"
    ERROR_TAMPERING_DETECTED: Final[str] = "License tampering detected"
    ERROR_ACTIVATION_LIMIT: Final[str] = "Maximum activations reached"
    ERROR_SERVER_OFFLINE: Final[str] = "License server is offline"
    ERROR_INVALID_SIGNATURE: Final[str] = "Invalid digital signature"
    ERROR_SUBSCRIPTION_EXPIRED: Final[str] = "Subscription has expired"
    ERROR_NETWORK: Final[str] = "Network error occurred"
    ERROR_DATABASE: Final[str] = "Database error occurred"
    ERROR_PERMISSION: Final[str] = "Permission denied"
    ERROR_NOT_FOUND: Final[str] = "Resource not found"
    ERROR_VALIDATION: Final[str] = "Validation error"
    ERROR_INTERNAL: Final[str] = "Internal server error"

    # Success messages
    SUCCESS_ACTIVATION: Final[str] = "License activated successfully"
    SUCCESS_VALIDATION: Final[str] = "License validated successfully"
    SUCCESS_RENEWAL: Final[str] = "License renewed successfully"
    SUCCESS_REVOCATION: Final[str] = "License revoked successfully"
    SUCCESS_GENERATION: Final[str] = "License generated successfully"
    SUCCESS_DEACTIVATION: Final[str] = "License deactivated successfully"

    # Feature descriptions
    FEATURE_DESCRIPTIONS: Final[dict[str, str]] = {
        Feature.REPORTING.value: "Advanced reporting and analytics",
        Feature.AI_MODULE.value: "AI-powered features and predictions",
        Feature.EXPORT.value: "Export data to PDF, Excel, and CSV",
        Feature.API_ACCESS.value: "REST API access for integration",
        Feature.CLOUD_SYNC.value: "Cloud synchronization across devices",
        Feature.BACKUP.value: "Automated backup and restore",
        Feature.PREMIUM_DASHBOARD.value: "Premium dashboard with advanced metrics",
        Feature.MULTI_USER.value: "Multi-user support with roles",
        Feature.ADVANCED_ANALYTICS.value: "Advanced analytics and insights",
        Feature.CUSTOM_INTEGRATION.value: "Custom third-party integrations",
    }

    # License type descriptions
    LICENSE_TYPE_DESCRIPTIONS: Final[dict[str, str]] = {
        LicenseType.TRIAL.value: "30-day trial with limited features",
        LicenseType.LIFETIME.value: "Lifetime license with all features",
        LicenseType.MONTHLY.value: "Monthly subscription with full features",
        LicenseType.YEARLY.value: "Yearly subscription with full features",
        LicenseType.ENTERPRISE.value: "Enterprise license with all features and support",
    }

    # Theme colors
    THEME_PRIMARY: Final[str] = "#2196F3"
    THEME_SECONDARY: Final[str] = "#FF9800"
    THEME_SUCCESS: Final[str] = "#4CAF50"
    THEME_ERROR: Final[str] = "#F44336"
    THEME_WARNING: Final[str] = "#FFC107"
    THEME_INFO: Final[str] = "#00BCD4"
    THEME_BACKGROUND: Final[str] = "#1E1E1E"
    THEME_SURFACE: Final[str] = "#2D2D2D"
    THEME_TEXT: Final[str] = "#FFFFFF"
    THEME_TEXT_SECONDARY: Final[str] = "#B0B0B0"