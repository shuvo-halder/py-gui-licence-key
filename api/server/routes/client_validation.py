"""
Client SDK validation and activation API router.

Provides endpoints that the generated client SDK communicates with
for license activation, validation, and deactivation.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.logger import get_logger
from database import async_session_factory
from services.encryption.service import EncryptionService
from services.licensing.service import LicensingService
from services.hardware.service import HardwareService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Client SDK"])


# --- Pydantic Models ---

class ClientActivateRequest(BaseModel):
    """Request from client SDK to activate a license."""
    app_id: str
    license_key: str
    machine_fingerprint: str


class ClientValidateRequest(BaseModel):
    """Request from client SDK to validate a license."""
    app_id: str
    license_key: str
    machine_fingerprint: str


class ClientDeactivateRequest(BaseModel):
    """Request from client SDK to deactivate a license."""
    app_id: str
    license_key: str
    machine_fingerprint: str


# --- Dependencies ---

async def get_services():
    """Get services for client SDK operations."""
    async with async_session_factory() as session:
        encryption = EncryptionService()
        hardware = HardwareService()
        licensing = LicensingService(session, encryption, hardware)
        yield licensing


# --- Endpoints ---

@router.post("/client/activate", response_model=dict[str, Any])
async def client_activate(
    request: ClientActivateRequest,
    services: LicensingService = Depends(get_services),
) -> dict[str, Any]:
    """
    Activate a license from the client SDK.

    Validates the license key, registers the machine, and returns
    signed license data for local storage.

    Args:
        request: Activation request with app_id, license_key, machine_fingerprint.

    Returns:
        Response with activation status and signed license data.
    """
    try:
        result = await services.validate_license(
            license_key=request.license_key,
            machine_fingerprint=request.machine_fingerprint,
        )

        if not result.get("valid"):
            return {
                "activated": False,
                "message": result.get("message", "License validation failed"),
                "reason": result.get("reason", "invalid"),
            }

        # Generate signed license data for client storage
        encryption = EncryptionService()
        license_data = {
            "license_key": request.license_key,
            "app_id": request.app_id,
            "machine_fingerprint": request.machine_fingerprint,
            "valid": True,
            "activated": True,
            "activated_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

        # Sign the license data
        signature = encryption.sign_data(license_data)
        license_data["signature"] = signature

        return {
            "activated": True,
            "message": "License activated successfully",
            "license_data": license_data,
        }

    except ValueError as e:
        return {
            "activated": False,
            "message": str(e),
            "reason": "validation_error",
        }
    except Exception as e:
        logger.error(f"Client activation failed: {e}")
        return {
            "activated": False,
            "message": "Server error during activation",
            "reason": "server_error",
        }


@router.post("/client/validate", response_model=dict[str, Any])
async def client_validate(
    request: ClientValidateRequest,
    services: LicensingService = Depends(get_services),
) -> dict[str, Any]:
    """
    Validate a license from the client SDK.

    Performs full validation including license existence,
    expiration, machine binding, and revocation status.

    Args:
        request: Validation request with app_id, license_key, machine_fingerprint.

    Returns:
        Validation result with status and details.
    """
    try:
        result = await services.validate_license(
            license_key=request.license_key,
            machine_fingerprint=request.machine_fingerprint,
        )

        return {
            "valid": result.get("valid", False),
            "message": result.get("message", "Validation completed"),
            "reason": result.get("reason", "unknown"),
            "license_type": result.get("license_type"),
            "expires_at": result.get("expires_at"),
            "features": result.get("features", []),
        }

    except Exception as e:
        logger.error(f"Client validation failed: {e}")
        return {
            "valid": False,
            "message": "Server error during validation",
            "reason": "server_error",
        }


@router.post("/client/deactivate", response_model=dict[str, Any])
async def client_deactivate(
    request: ClientDeactivateRequest,
    services: LicensingService = Depends(get_services),
) -> dict[str, Any]:
    """
    Deactivate a license from the client SDK.

    Removes the machine binding for the specified license key.

    Args:
        request: Deactivation request with app_id, license_key, machine_fingerprint.

    Returns:
        Deactivation result.
    """
    try:
        result = await services.revoke_license(
            license_key=request.license_key,
            reason="Client deactivation request",
        )

        return {
            "deactivated": result,
            "message": "License deactivated successfully" if result else "Deactivation failed",
        }

    except Exception as e:
        logger.error(f"Client deactivation failed: {e}")
        return {
            "deactivated": False,
            "message": f"Deactivation error: {e}",
        }