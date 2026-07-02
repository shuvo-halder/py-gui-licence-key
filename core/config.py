"""
Application configuration management using Pydantic Settings.

This module provides type-safe configuration loading from environment variables,
configuration files, and defaults. It supports both development and production
environments with secure secret management.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Loads configuration from environment variables, .env file, and defaults.
    Provides typed access to all configuration parameters with validation.

    Attributes:
        APP_NAME: Application name.
        APP_VERSION: Application version.
        APP_ENV: Environment (development, staging, production).
        DEBUG: Debug mode flag.
        SECRET_KEY: Master secret key for encryption.
        DATABASE_URL: SQLite database URL for local storage.
        POSTGRES_URL: PostgreSQL database URL for server.
        API_HOST: API server host.
        API_PORT: API server port.
        API_WORKERS: Number of API workers.
        CORS_ORIGINS: Allowed CORS origins.
        JWT_SECRET: JWT signing secret.
        JWT_ALGORITHM: JWT signing algorithm.
        JWT_EXPIRY: JWT token expiry in minutes.
        RSA_KEY_SIZE: RSA key size in bits.
        AES_KEY_SIZE: AES key size in bits.
        LICENSE_DIR: Directory for license files.
        LOG_LEVEL: Logging level.
        LOG_DIR: Directory for log files.
        BACKUP_DIR: Directory for backups.
        MAX_LOGIN_ATTEMPTS: Maximum failed login attempts.
        RATE_LIMIT: API rate limit per minute.
    """

    # Application
    APP_NAME: str = Field(default="Software License Manager", alias="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    DEBUG: bool = Field(default=False, alias="DEBUG")

    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        alias="SECRET_KEY",
        min_length=32,
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/license_manager.db",
        alias="DATABASE_URL",
    )
    POSTGRES_URL: Optional[str] = Field(default=None, alias="POSTGRES_URL")

    # API
    API_HOST: str = Field(default="0.0.0.0", alias="API_HOST")
    API_PORT: int = Field(default=8000, alias="API_PORT", ge=1, le=65535)
    API_WORKERS: int = Field(default=4, alias="API_WORKERS", ge=1, le=32)
    CORS_ORIGINS: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    # JWT
    JWT_SECRET: str = Field(
        default="change-this-jwt-secret-in-production",
        alias="JWT_SECRET",
        min_length=32,
    )
    JWT_ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    JWT_EXPIRY: int = Field(default=60, alias="JWT_EXPIRY", ge=5)

    # Encryption
    RSA_KEY_SIZE: int = Field(default=4096, alias="RSA_KEY_SIZE", ge=2048)
    AES_KEY_SIZE: int = Field(default=256, alias="AES_KEY_SIZE", ge=128)

    # Paths
    LICENSE_DIR: str = Field(default="./licenses", alias="LICENSE_DIR")
    LOG_DIR: str = Field(default="./logs", alias="LOG_DIR")
    BACKUP_DIR: str = Field(default="./backups", alias="BACKUP_DIR")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")

    # Security settings
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, alias="MAX_LOGIN_ATTEMPTS", ge=1)
    RATE_LIMIT: int = Field(default=60, alias="RATE_LIMIT", ge=1)

    # Model configuration
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("APP_ENV")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Validate that environment is one of the allowed values."""
        allowed = {"development", "staging", "production"}
        if value.lower() not in allowed:
            msg = f"APP_ENV must be one of {allowed}, got {value}"
            raise ValueError(msg)
        return value.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate that log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value.upper() not in allowed:
            msg = f"LOG_LEVEL must be one of {allowed}, got {value}"
            raise ValueError(msg)
        return value.upper()

    @model_validator(mode="after")
    def create_directories(self) -> "Settings":
        """Create required directories on validation."""
        directories = [
            self.LICENSE_DIR,
            self.LOG_DIR,
            self.BACKUP_DIR,
            os.path.dirname(self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")),
        ]
        for directory in directories:
            if directory and directory != ".":
                Path(directory).mkdir(parents=True, exist_ok=True)
        return self

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for SQLAlchemy."""
        return self.DATABASE_URL.replace("+aiosqlite", "")

    def get_api_url(self) -> str:
        """Get the full API URL."""
        return f"http://{self.API_HOST}:{self.API_PORT}"

    def get_secure_api_url(self) -> str:
        """Get secure API URL for production."""
        return f"https://{self.API_HOST}:{self.API_PORT}"


# Global singleton instance
settings = Settings()