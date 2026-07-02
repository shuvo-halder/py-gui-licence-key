"""
Application logging configuration using Loguru.

This module provides centralized logging setup with rotation, retention,
and structured logging support. It creates both file and console handlers
with appropriate formatting for development and production environments.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _logger

from core.config import settings


def setup_logger(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "30 days",
) -> None:
    """
    Configure the application logger with file and console handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to settings.LOG_LEVEL.
        log_dir: Directory for log files. Defaults to settings.LOG_DIR.
        rotation: Log file rotation policy. Defaults to "10 MB".
        retention: Log retention policy. Defaults to "30 days".

    The logger is configured with:
    - Console handler with colored output for development
    - File handler with rotation and compression for production
    - Structured error logging with traceback support
    """
    level = (log_level or settings.LOG_LEVEL).upper()
    log_directory = Path(log_dir or settings.LOG_DIR)

    # Remove default handler
    _logger.remove()

    # Add console handler with colorized output
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    _logger.add(
        sys.stderr,
        format=console_format,
        level=level,
        colorize=True,
        diagnose=settings.DEBUG,
        backtrace=settings.DEBUG,
    )

    # Add file handler with rotation
    log_directory.mkdir(parents=True, exist_ok=True)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # Info log file
    _logger.add(
        str(log_directory / "app_{time:YYYY-MM-DD}.log"),
        format=file_format,
        level=level,
        rotation=rotation,
        retention=retention,
        compression="gz",
        enqueue=True,
    )

    # Error log file (separate file for errors only)
    _logger.add(
        str(log_directory / "error_{time:YYYY-MM-DD}.log"),
        format=file_format,
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression="gz",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Audit log file (for security-sensitive operations)
    audit_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}"
    _logger.add(
        str(log_directory / "audit_{time:YYYY-MM-DD}.log"),
        format=audit_format,
        level="INFO",
        rotation=rotation,
        retention="90 days",
        compression="gz",
        enqueue=True,
        filter=lambda record: record.get("extra", {}).get("audit", False),
    )

    _logger.info(
        "Logger initialized - Level: {level}, Directory: {directory}",
        level=level,
        directory=str(log_directory),
    )


def get_logger(name: Optional[str] = None):
    """
    Get a logger instance with optional contextual binding.

    Args:
        name: Optional name for the logger context. Typically __name__.

    Returns:
        A Loguru logger instance bound with contextual information.

    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
        logger.bind(audit=True).info("User login: admin")
    """
    return _logger.bind(name=name or __name__)


def log_audit(action: str, user: str, details: str = "") -> None:
    """
    Log an audit event for security-sensitive operations.

    Args:
        action: The audit action being performed.
        user: The user performing the action.
        details: Additional details about the action.

    Example:
        log_audit("login", "admin", "Successful login from IP 192.168.1.1")
    """
    _logger.bind(audit=True).info(
        "AUDIT | Action: {action} | User: {user} | Details: {details}",
        action=action,
        user=user,
        details=details,
    )


# Initialize logger on module import
setup_logger()

# Export the configured logger
logger = get_logger()