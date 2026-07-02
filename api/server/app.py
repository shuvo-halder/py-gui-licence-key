"""
FastAPI application server for the License Manager API.

Provides REST API endpoints for license management, activation,
validation, subscription management, and machine registration.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from core.config import settings
from core.constants import (
    Constants,
    LicenseType,
    SubscriptionInterval,
    SubscriptionStatus,
)
from core.logger import get_logger
from database import init_database, close_database, get_session, async_session_factory
from services.encryption.service import EncryptionService
from services.hardware.service import HardwareService
from services.licensing.service import LicensingService
from services.activation.service import ActivationService
from services.subscription.service import SubscriptionService

logger = get_logger(__name__)
security = HTTPBearer()


# --- Pydantic Models ---

class LicenseGenerateRequest(BaseModel):
    license_type: LicenseType
    customer_id: str
    product_id: str
    customer_name: str
    customer_email: str
    enabled_features: list[str] = []
    duration_days: Optional[int] = None
    max_machines: int = 5


class LicenseActivateRequest(BaseModel):
    license_key: str
    customer_id: str
    machine_name: Optional[str] = None


class LicenseValidateRequest(BaseModel):
    license_key: str
    machine_fingerprint: Optional[str] = None


class LicenseRevokeRequest(BaseModel):
    license_key: str
    reason: str = ""


class SubscriptionCreateRequest(BaseModel):
    license_id: str
    customer_id: str
    product_id: str
    interval: SubscriptionInterval
    amount: Optional[float] = None
    currency: str = "USD"
    auto_renew: bool = True


class SubscriptionRenewRequest(BaseModel):
    license_id: str
    payment_reference: str = ""


class MachineRegisterRequest(BaseModel):
    license_key: str
    customer_id: str
    machine_name: Optional[str] = None


class MachineBlacklistRequest(BaseModel):
    machine_fingerprint: str
    reason: str


class LicenseTransferRequest(BaseModel):
    license_key: str
    new_customer_id: str


# --- Service Dependencies ---

async def get_encryption_service() -> EncryptionService:
    """Get encryption service instance."""
    return EncryptionService()


async def get_hardware_service() -> HardwareService:
    """Get hardware service instance."""
    return HardwareService()


async def get_licensing_service(
    encryption: EncryptionService = Depends(get_encryption_service),
    hardware: HardwareService = Depends(get_hardware_service),
) -> LicensingService:
    """Get licensing service with session."""
    async with async_session_factory() as session:
        yield LicensingService(session, encryption, hardware)


async def get_activation_service(
    encryption: EncryptionService = Depends(get_encryption_service),
    hardware: HardwareService = Depends(get_hardware_service),
) -> ActivationService:
    """Get activation service with session."""
    async with async_session_factory() as session:
        yield ActivationService(session, encryption, hardware)


async def get_subscription_service() -> SubscriptionService:
    """Get subscription service with session."""
    async with async_session_factory() as session:
        yield SubscriptionService(session)


# --- Application Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting License Manager API server...")
    await init_database()
    yield
    await close_database()
    logger.info("License Manager API server stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise License Management API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check ---

@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# --- License Endpoints ---

@app.post("/api/v1/generate-license", tags=["Licenses"])
async def generate_license(
    request: LicenseGenerateRequest,
    service: LicensingService = Depends(get_licensing_service),
) -> dict[str, Any]:
    """Generate a new cryptographically signed license."""
    try:
        result = await service.generate_license(
            license_type=request.license_type,
            customer_id=request.customer_id,
            product_id=request.product_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            enabled_features=request.enabled_features,
            duration_days=request.duration_days,
            max_machines=request.max_machines,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"License generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/activate", tags=["Activation"])
async def activate_license(
    request: LicenseActivateRequest,
    service: ActivationService = Depends(get_activation_service),
) -> dict[str, Any]:
    """Activate a license online."""
    try:
        result = await service.activate_online(
            license_key=request.license_key,
            customer_id=request.customer_id,
            machine_name=request.machine_name,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/validate", tags=["Licenses"])
async def validate_license(
    request: LicenseValidateRequest,
    service: LicensingService = Depends(get_licensing_service),
) -> dict[str, Any]:
    """Validate a license."""
    try:
        result = await service.validate_license(
            license_key=request.license_key,
            machine_fingerprint=request.machine_fingerprint,
        )
        return {"success": result["valid"], "data": result}
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/renew", tags=["Subscriptions"])
async def renew_subscription(
    request: SubscriptionRenewRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """Renew a subscription."""
    try:
        result = await service.renew_subscription(
            license_id=request.license_id,
            payment_reference=request.payment_reference,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Renewal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/revoke", tags=["Licenses"])
async def revoke_license(
    request: LicenseRevokeRequest,
    service: LicensingService = Depends(get_licensing_service),
) -> dict[str, Any]:
    """Revoke a license."""
    try:
        result = await service.revoke_license(
            license_key=request.license_key,
            reason=request.reason,
        )
        return {"success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Revocation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/machine/register", tags=["Machines"])
async def register_machine(
    request: MachineRegisterRequest,
    service: ActivationService = Depends(get_activation_service),
) -> dict[str, Any]:
    """Register a machine for license activation."""
    try:
        result = await service.activate_online(
            license_key=request.license_key,
            customer_id=request.customer_id,
            machine_name=request.machine_name,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Machine registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/machine/remove", tags=["Machines"])
async def remove_machine(
    license_key: str = Form(...),
    machine_fingerprint: Optional[str] = Form(None),
    service: ActivationService = Depends(get_activation_service),
) -> dict[str, Any]:
    """Remove/deactivate a machine from a license."""
    try:
        result = await service.deactivate(
            license_key=license_key,
            machine_fingerprint=machine_fingerprint,
        )
        return {"success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Machine removal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/subscription/update", tags=["Subscriptions"])
async def update_subscription(
    license_id: str = Form(...),
    status: SubscriptionStatus = Form(...),
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """Update subscription status."""
    try:
        result = await service.update_subscription_status(
            license_id=license_id,
            status=status,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscription update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/offline-activation", tags=["Activation"])
async def offline_activation(
    license_key: str = Form(...),
    request_file: UploadFile = File(...),
    service: LicensingService = Depends(get_licensing_service),
) -> dict[str, Any]:
    """Process offline activation request."""
    try:
        # Save uploaded request file
        request_path = f"/tmp/{request_file.filename}"
        content = await request_file.read()
        with open(request_path, "wb") as f:
            f.write(content)

        # Process offline activation
        activation_path = await service.activate_offline(
            license_key=license_key,
            request_file_path=request_path,
        )

        return {
            "success": True,
            "data": {
                "activation_file": activation_path,
                "message": "Offline activation file generated",
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Offline activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Statistics Endpoints ---

@app.get("/api/v1/stats/licenses", tags=["Statistics"])
async def get_license_stats(
    service: LicensingService = Depends(get_licensing_service),
) -> dict[str, Any]:
    """Get license statistics."""
    try:
        stats = await service.get_license_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Failed to get license stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats/subscriptions", tags=["Statistics"])
async def get_subscription_stats(
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """Get subscription statistics."""
    try:
        stats = await service.get_subscription_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Failed to get subscription stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Machine Management ---

@app.post("/api/v1/machine/blacklist", tags=["Machines"])
async def blacklist_machine(
    request: MachineBlacklistRequest,
    service: ActivationService = Depends(get_activation_service),
) -> dict[str, Any]:
    """Blacklist a machine."""
    try:
        result = await service.blacklist_machine(
            machine_fingerprint=request.machine_fingerprint,
            reason=request.reason,
        )
        return {"success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Machine blacklist failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/license/transfer", tags=["Licenses"])
async def transfer_license(
    request: LicenseTransferRequest,
    service: ActivationService = Depends(get_activation_service),
) -> dict[str, Any]:
    """Transfer a license to a new customer."""
    try:
        result = await service.transfer_license(
            license_key=request.license_key,
            new_customer_id=request.new_customer_id,
        )
        return {"success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"License transfer failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Subscription Management ---

@app.post("/api/v1/subscription/create", tags=["Subscriptions"])
async def create_subscription(
    request: SubscriptionCreateRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """Create a new subscription."""
    try:
        result = await service.create_subscription(
            license_id=request.license_id,
            customer_id=request.customer_id,
            product_id=request.product_id,
            interval=request.interval,
            amount=request.amount,
            currency=request.currency,
            auto_renew=request.auto_renew,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/subscription/cancel", tags=["Subscriptions"])
async def cancel_subscription(
    license_id: str = Form(...),
    reason: str = Form(""),
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """Cancel a subscription."""
    try:
        result = await service.cancel_subscription(
            license_id=license_id,
            reason=reason,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Public Key Endpoint ---

@app.get("/api/v1/public-key", tags=["Security"])
async def get_public_key(
    encryption: EncryptionService = Depends(get_encryption_service),
) -> dict[str, Any]:
    """Get the public key for license verification."""
    try:
        return {
            "success": True,
            "data": {
                "public_key": encryption.get_public_key_pem(),
                "fingerprint": encryption.get_key_fingerprint(),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get public key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Error Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return {
        "success": False,
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
        },
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "success": False,
        "error": {
            "code": 500,
            "message": "Internal server error",
        },
    }