"""
Licensing service for license generation, validation, and management.

This service handles:
- License key generation with cryptographic signing
- License type management (trial, lifetime, monthly, yearly, enterprise)
- Feature-based licensing
- License validation and verification
- Anti-tampering and clock manipulation detection
"""

from __future__ import annotations

import json
import os
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.constants import (
    Constants,
    LicenseType,
    ActivationStatus,
    ValidationResult,
)
from core.logger import get_logger
from database.repository.license_repository import LicenseRepository
from database.repository.product_repository import ProductRepository
from database.repository.customer_repository import CustomerRepository
from database.repository.activation_repository import ActivationRepository
from services.encryption.service import EncryptionService
from services.hardware.service import HardwareService

logger = get_logger(__name__)


class LicensingService:
    """
    Service for license lifecycle management.

    Provides comprehensive license generation, validation, and management
    with cryptographic security and anti-tampering measures.
    """

    def __init__(
        self,
        session: AsyncSession,
        encryption_service: EncryptionService,
        hardware_service: HardwareService,
    ) -> None:
        """
        Initialize the licensing service.

        Args:
            session: Database session.
            encryption_service: Service for cryptographic operations.
            hardware_service: Service for hardware fingerprinting.
        """
        self.session = session
        self.encryption = encryption_service
        self.hardware = hardware_service
        self.license_repo = LicenseRepository(session)
        self.product_repo = ProductRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.activation_repo = ActivationRepository(session)

    def generate_license_key(self) -> str:
        """
        Generate a cryptographically secure license key.

        Format: XXXX-XXXX-XXXX-XXXX (32 hex characters in 4 segments)

        Returns:
            A formatted license key string.
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(16)
        hex_string = random_bytes.hex().upper()

        # Split into segments
        segments = []
        segment_length = Constants.LICENSE_KEY_SEGMENT_LENGTH
        for i in range(Constants.LICENSE_KEY_SEGMENTS):
            start = i * segment_length
            end = start + segment_length
            segments.append(hex_string[start:end])

        return "-".join(segments)

    async def generate_license(
        self,
        license_type: LicenseType,
        customer_id: str,
        product_id: str,
        customer_name: str,
        customer_email: str,
        enabled_features: Optional[list[str]] = None,
        duration_days: Optional[int] = None,
        max_machines: int = 5,
    ) -> dict[str, Any]:
        """
        Generate a new cryptographically signed license.

        Args:
            license_type: Type of license to generate.
            customer_id: UUID of the customer.
            product_id: UUID of the product.
            customer_name: Customer's full name.
            customer_email: Customer's email address.
            enabled_features: List of enabled features.
            duration_days: Custom duration in days (overrides type default).
            max_machines: Maximum number of allowed machines.

        Returns:
            Dictionary containing the generated license data.
        """
        # Verify customer exists
        customer = await self.customer_repo.get(customer_id)
        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")

        # Verify product exists
        product = await self.product_repo.get(product_id)
        if not product:
            raise ValueError(f"Product not found: {product_id}")

        # Generate license key
        license_key = self.generate_license_key()

        # Calculate expiration
        now = datetime.utcnow()
        is_perpetual = False

        if duration_days:
            expires_at = now + timedelta(days=duration_days)
        elif license_type == LicenseType.TRIAL:
            expires_at = now + timedelta(days=Constants.TRIAL_DAYS)
        elif license_type == LicenseType.LIFETIME:
            expires_at = None
            is_perpetual = True
        elif license_type == LicenseType.MONTHLY:
            expires_at = now + timedelta(days=30)
        elif license_type == LicenseType.YEARLY:
            expires_at = now + timedelta(days=365)
        elif license_type == LicenseType.ENTERPRISE:
            expires_at = now + timedelta(days=365 * 5)  # 5 years
        else:
            expires_at = now + timedelta(days=Constants.TRIAL_DAYS)

        # Build license data for signing
        license_data = {
            "license_key": license_key,
            "license_type": license_type.value,
            "customer_id": customer_id,
            "product_id": product_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "product_name": product.name,
            "product_version": product.version,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_perpetual": is_perpetual,
            "enabled_features": enabled_features or [],
            "max_machines": max_machines,
        }

        # Sign the license data
        signature = self.encryption.generate_license_signature(license_data)

        # Save to database
        license_model = await self.license_repo.create(
            license_key=license_key,
            license_type=license_type,
            product_id=product_id,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            product_name=product.name,
            product_version=product.version,
            issued_at=now,
            expires_at=expires_at,
            is_perpetual=is_perpetual,
            enabled_features=enabled_features or [],
            max_machines=max_machines,
            signature=signature,
            status=ActivationStatus.PENDING,
        )

        logger.info(
            "License generated: {key} ({type}) for {customer}",
            key=license_key[:16] + "...",
            type=license_type.value,
            customer=customer_name,
        )

        return {
            **license_model.to_dict(),
            "signature": signature,
        }

    async def validate_license(
        self,
        license_key: str,
        machine_fingerprint: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Validate a license with comprehensive checks.

        Performs validation of:
        - License existence and status
        - Cryptographic signature
        - Expiration date
        - Clock manipulation
        - Machine binding (if fingerprint provided)
        - Subscription status
        - Revocation status

        Args:
            license_key: The license key to validate.
            machine_fingerprint: Optional machine fingerprint for hardware binding.

        Returns:
            Dictionary with validation results and license data.
        """
        result = {
            "valid": False,
            "result": ValidationResult.INVALID,
            "license_data": None,
            "message": "",
        }

        try:
            # Get license from database
            license_model = await self.license_repo.get_by_license_key(license_key)
            if not license_model:
                result["message"] = Constants.ERROR_INVALID_LICENSE
                return result

            license_data = license_model.to_dict()

            # Check revocation status
            if license_model.is_revoked:
                result["result"] = ValidationResult.REVOKED
                result["message"] = Constants.ERROR_REVOKED_LICENSE
                return result

            # Verify cryptographic signature
            if license_model.signature:
                sig_valid = self.encryption.verify_license_signature(
                    license_data, license_model.signature
                )
                if not sig_valid:
                    result["result"] = ValidationResult.TAMPERED
                    result["message"] = Constants.ERROR_TAMPERING_DETECTED
                    return result

            # Check expiration
            if not license_model.is_perpetual and license_model.expires_at:
                if datetime.utcnow() > license_model.expires_at:
                    result["result"] = ValidationResult.EXPIRED
                    result["message"] = Constants.ERROR_EXPIRED_LICENSE
                    return result

            # Check clock manipulation
            if self._detect_clock_manipulation(license_model):
                result["result"] = ValidationResult.CLOCK_MANIPULATED
                result["message"] = Constants.ERROR_CLOCK_MANIPULATION
                return result

            # Verify machine binding
            if machine_fingerprint:
                machine_match = await self._verify_machine_binding(
                    license_model.id, machine_fingerprint
                )
                if not machine_match:
                    result["result"] = ValidationResult.MACHINE_MISMATCH
                    result["message"] = Constants.ERROR_MACHINE_MISMATCH
                    return result

            # Check subscription if it exists
            if license_model.subscription:
                if not license_model.subscription.is_active():
                    if license_model.subscription.is_in_grace_period():
                        # Still valid but warn
                        pass
                    else:
                        result["result"] = ValidationResult.SUBSCRIPTION_EXPIRED
                        result["message"] = Constants.ERROR_SUBSCRIPTION_EXPIRED
                        return result

            # All checks passed
            result["valid"] = True
            result["result"] = ValidationResult.VALID
            result["license_data"] = license_data
            result["message"] = Constants.SUCCESS_VALIDATION

            # Update validation count
            await self.license_repo.update(
                license_model.id,
                status=ActivationStatus.ACTIVATED,
            )

            # Update last validated timestamp via activation record
            activations = await self.activation_repo.get_by_license_id(license_model.id)
            if activations:
                latest = activations[-1]
                await self.activation_repo.update(
                    latest.id,
                    last_validated_at=datetime.utcnow(),
                    validation_count=latest.validation_count + 1,
                )

            logger.info(
                "License validated: {key} -> {result}",
                key=license_key[:16] + "...",
                result=result["result"].value,
            )

        except Exception as e:
            logger.error(f"License validation error: {e}")
            result["message"] = str(e)

        return result

    async def revoke_license(self, license_key: str, reason: str = "") -> bool:
        """
        Revoke a license, making it permanently invalid.

        Args:
            license_key: License key to revoke.
            reason: Reason for revocation.

        Returns:
            True if successfully revoked.
        """
        license_model = await self.license_repo.get_by_license_key(license_key)
        if not license_model:
            raise ValueError(f"License not found: {license_key}")

        await self.license_repo.update(
            license_model.id,
            is_revoked=True,
            revoked_at=datetime.utcnow(),
            revocation_reason=reason or "No reason provided",
            status=ActivationStatus.REVOKED,
        )

        logger.warning(
            "License revoked: {key} - {reason}",
            key=license_key[:16] + "...",
            reason=reason or "No reason",
        )

        return True

    async def activate_offline(
        self, license_key: str, request_file_path: str
    ) -> str:
        """
        Process offline activation request.

        Args:
            license_key: License key to activate.
            request_file_path: Path to the machine request file.

        Returns:
            Path to the generated activation file.
        """
        # Read and verify request file
        request_data = self.encryption.decrypt_license_file(request_file_path)
        
        # Validate the request
        validation = await self.validate_license(
            license_key,
            machine_fingerprint=request_data.get("machine_fingerprint"),
        )

        if not validation["valid"]:
            raise ValueError(f"License validation failed: {validation['message']}")

        # Generate activation response
        activation_data = {
            "license_key": license_key,
            "activated_at": datetime.utcnow().isoformat(),
            "machine_fingerprint": request_data.get("machine_fingerprint"),
            "machine_name": request_data.get("machine_name"),
            "signature": self.encryption.generate_license_signature(
                {"license_key": license_key, "activated_at": str(datetime.utcnow())}
            ),
        }

        # Save activation file
        activation_dir = Path(settings.LICENSE_DIR)
        activation_dir.mkdir(parents=True, exist_ok=True)
        activation_path = str(activation_dir / f"activation_{license_key[:8]}.lic")

        self.encryption.encrypt_license_file(activation_data, activation_path)

        logger.info(
            "Offline activation file generated: {path}",
            path=activation_path,
        )

        return activation_path

    def generate_machine_request_file(self, output_path: str) -> str:
        """
        Generate a machine request file for offline activation.

        Args:
            output_path: Path to save the request file.

        Returns:
            Path to the generated request file.
        """
        machine_data = {
            "machine_fingerprint": self.hardware.get_fingerprint(),
            "machine_name": self.hardware.get_machine_name(),
            "hostname": self.hardware.get_hostname(),
            "os_info": self.hardware.get_os_info(),
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Ensure proper extension
        if not output_path.endswith(Constants.REQUEST_FILE_EXTENSION):
            output_path += Constants.REQUEST_FILE_EXTENSION

        self.encryption.encrypt_license_file(machine_data, output_path)

        logger.info(f"Machine request file generated: {output_path}")
        return output_path

    async def activate_from_file(self, activation_file_path: str) -> bool:
        """
        Activate license from an activation file (offline activation).

        Args:
            activation_file_path: Path to the activation file.

        Returns:
            True if activation was successful.
        """
        try:
            activation_data = self.encryption.decrypt_license_file(
                activation_file_path
            )

            # Verify signature
            sig_valid = self.encryption.verify_license_signature(
                activation_data,
                activation_data.get("signature", ""),
            )

            if not sig_valid:
                raise ValueError("Invalid activation file signature")

            # Validate the license
            validation = await self.validate_license(
                activation_data["license_key"],
                machine_fingerprint=activation_data.get("machine_fingerprint"),
            )

            if not validation["valid"]:
                raise ValueError(f"License validation failed: {validation['message']}")

            logger.info(
                "License activated from file: {key}",
                key=activation_data["license_key"][:16] + "...",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to activate from file: {e}")
            raise

    def _detect_clock_manipulation(self, license_model: Any) -> bool:
        """
        Detect system clock manipulation attempts.

        Checks if the system clock has been rolled back significantly.

        Args:
            license_model: The license model instance.

        Returns:
            True if clock manipulation is suspected.
        """
        try:
            # Check if license was issued in the future
            if license_model.issued_at and license_model.issued_at > datetime.utcnow():
                return True

            # Check if last validation was in the future
            activations = license_model.activations
            if activations:
                latest = activations[-1]
                if (
                    latest.last_validated_at
                    and latest.last_validated_at > datetime.utcnow()
                ):
                    return True

            return False

        except Exception as e:
            logger.error(f"Clock manipulation detection error: {e}")
            return False

    async def _verify_machine_binding(
        self, license_id: str, machine_fingerprint: str
    ) -> bool:
        """
        Verify that the machine fingerprint matches an activated machine.

        Args:
            license_id: UUID of the license.
            machine_fingerprint: Machine fingerprint to verify.

        Returns:
            True if machine is bound to this license.
        """
        from database.repository.machine_repository import MachineRepository

        machine_repo = MachineRepository(self.session)
        machines = await machine_repo.get_machines_by_license(license_id)

        for machine in machines:
            if machine.machine_fingerprint == machine_fingerprint:
                return True

        return False

    async def get_license_statistics(self) -> dict[str, Any]:
        """
        Get license statistics for the dashboard.

        Returns:
            Dictionary of license statistics.
        """
        total = await self.license_repo.count()
        active = await self.license_repo.count(
            {"status": ActivationStatus.ACTIVATED, "is_revoked": False}
        )
        expired = len(await self.license_repo.get_expired_licenses())
        revoked = await self.license_repo.count({"is_revoked": True})
        pending = await self.license_repo.count({"status": ActivationStatus.PENDING})

        return {
            "total": total,
            "active": active,
            "expired": expired,
            "revoked": revoked,
            "pending": pending,
            "utilization": round((active / total * 100), 2) if total > 0 else 0,
        }