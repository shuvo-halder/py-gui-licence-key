"""
Activation service for managing license activations.

Handles online and offline activation workflows, machine registration,
and activation lifecycle management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import (
    Constants,
    ActivationStatus,
    MachineStatus,
    ValidationResult,
)
from core.logger import get_logger
from database.repository.activation_repository import ActivationRepository
from database.repository.license_repository import LicenseRepository
from database.repository.machine_repository import MachineRepository
from database.repository.customer_repository import CustomerRepository
from services.encryption.service import EncryptionService
from services.hardware.service import HardwareService

logger = get_logger(__name__)


class ActivationService:
    """
    Service for managing license activations.

    Supports both online and offline activation workflows with
    machine registration and hardware binding.
    """

    def __init__(
        self,
        session: AsyncSession,
        encryption_service: EncryptionService,
        hardware_service: HardwareService,
    ) -> None:
        """
        Initialize the activation service.

        Args:
            session: Database session.
            encryption_service: Service for cryptographic operations.
            hardware_service: Service for hardware fingerprinting.
        """
        self.session = session
        self.encryption = encryption_service
        self.hardware = hardware_service
        self.activation_repo = ActivationRepository(session)
        self.license_repo = LicenseRepository(session)
        self.machine_repo = MachineRepository(session)
        self.customer_repo = CustomerRepository(session)

    async def activate_online(
        self,
        license_key: str,
        customer_id: str,
        machine_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Perform online activation of a license.

        Args:
            license_key: The license key to activate.
            customer_id: UUID of the customer.
            machine_name: Optional name for the machine.

        Returns:
            Dictionary with activation result and data.
        """
        # Get license
        license_model = await self.license_repo.get_by_license_key(license_key)
        if not license_model:
            raise ValueError(Constants.ERROR_INVALID_LICENSE)

        # Check activation limit
        machines = await self.machine_repo.get_machines_by_license(license_model.id)
        active_machines = [m for m in machines if m.status == MachineStatus.ACTIVE]

        if len(active_machines) >= license_model.max_machines:
            raise ValueError(Constants.ERROR_ACTIVATION_LIMIT)

        # Generate machine fingerprint
        fingerprint = self.hardware.get_fingerprint()

        # Check if machine is already registered
        existing_machine = await self.machine_repo.get_by_fingerprint(fingerprint)
        if existing_machine:
            if existing_machine.is_blacklisted:
                raise ValueError("Machine is blacklisted")
            if existing_machine.status == MachineStatus.ACTIVE:
                # Already activated, return existing activation
                activations = await self.activation_repo.get_by_machine_id(
                    existing_machine.id
                )
                return {
                    "activated": True,
                    "machine": existing_machine.to_dict(),
                    "activation": activations[-1].to_dict() if activations else None,
                }

        # Register machine
        machine = await self.machine_repo.create(
            customer_id=customer_id,
            license_id=license_model.id,
            machine_name=machine_name or self.hardware.get_machine_name(),
            machine_fingerprint=fingerprint,
            cpu_serial=self.hardware.get_cpu_serial(),
            motherboard_serial=self.hardware.get_motherboard_serial(),
            bios_serial=self.hardware.get_bios_serial(),
            disk_serial=self.hardware.get_disk_serial(),
            mac_address=self.hardware.get_mac_address(),
            machine_guid=self.hardware.get_machine_guid(),
            hostname=self.hardware.get_hostname(),
            os_info=self.hardware.get_os_info(),
            status=MachineStatus.ACTIVE,
            activated_at=datetime.utcnow(),
        )

        # Create activation record
        activation = await self.activation_repo.create(
            license_id=license_model.id,
            customer_id=customer_id,
            machine_id=machine.id,
            activation_type="online",
            status=ActivationStatus.ACTIVATED,
            machine_fingerprint=fingerprint,
            machine_name=machine.machine_name,
            hostname=self.hardware.get_hostname(),
            activated_at=datetime.utcnow(),
        )

        # Update license status
        await self.license_repo.update(
            license_model.id,
            status=ActivationStatus.ACTIVATED,
        )

        logger.info(
            "Online activation successful: {key} on {machine}",
            key=license_key[:16] + "...",
            machine=machine.machine_name,
        )

        return {
            "activated": True,
            "machine": machine.to_dict(),
            "activation": activation.to_dict(),
        }

    async def deactivate(
        self,
        license_key: str,
        machine_fingerprint: Optional[str] = None,
    ) -> bool:
        """
        Deactivate a license on a specific machine.

        Args:
            license_key: License key to deactivate.
            machine_fingerprint: Optional machine fingerprint to deactivate.

        Returns:
            True if deactivation was successful.
        """
        license_model = await self.license_repo.get_by_license_key(license_key)
        if not license_model:
            raise ValueError(Constants.ERROR_INVALID_LICENSE)

        if machine_fingerprint:
            machine = await self.machine_repo.get_by_fingerprint(machine_fingerprint)
            if machine:
                await self.machine_repo.update(
                    machine.id,
                    status=MachineStatus.INACTIVE,
                    deactivated_at=datetime.utcnow(),
                )

                # Update related activations
                activations = await self.activation_repo.get_by_machine_id(machine.id)
                for activation in activations:
                    await self.activation_repo.update(
                        activation.id,
                        status=ActivationStatus.DEACTIVATED,
                        deactivated_at=datetime.utcnow(),
                    )

        logger.info(
            "License deactivated: {key}",
            key=license_key[:16] + "...",
        )

        return True

    async def get_activation_status(self, license_key: str) -> dict[str, Any]:
        """
        Get the activation status of a license.

        Args:
            license_key: License key to check.

        Returns:
            Dictionary with activation status information.
        """
        license_model = await self.license_repo.get_by_license_key(license_key)
        if not license_model:
            raise ValueError(Constants.ERROR_INVALID_LICENSE)

        machines = await self.machine_repo.get_machines_by_license(license_model.id)
        activations = await self.activation_repo.get_by_license_id(license_model.id)

        return {
            "license_key": license_key,
            "status": license_model.status.value,
            "total_machines": len(machines),
            "active_machines": len(
                [m for m in machines if m.status == MachineStatus.ACTIVE]
            ),
            "max_machines": license_model.max_machines,
            "machines": [m.to_dict() for m in machines],
            "activations": [a.to_dict() for a in activations],
        }

    async def blacklist_machine(self, machine_fingerprint: str, reason: str) -> bool:
        """
        Blacklist a machine by its fingerprint.

        Args:
            machine_fingerprint: Machine fingerprint to blacklist.
            reason: Reason for blacklisting.

        Returns:
            True if machine was blacklisted.
        """
        machine = await self.machine_repo.get_by_fingerprint(machine_fingerprint)
        if not machine:
            raise ValueError("Machine not found")

        await self.machine_repo.update(
            machine.id,
            is_blacklisted=True,
            blacklist_reason=reason,
            status=MachineStatus.BLACKLISTED,
        )

        logger.warning(
            "Machine blacklisted: {fingerprint} - {reason}",
            fingerprint=machine_fingerprint[:16] + "...",
            reason=reason,
        )

        return True

    async def transfer_license(
        self, license_key: str, new_customer_id: str
    ) -> bool:
        """
        Transfer a license to a new customer.

        Args:
            license_key: License key to transfer.
            new_customer_id: UUID of the new customer.

        Returns:
            True if transfer was successful.
        """
        license_model = await self.license_repo.get_by_license_key(license_key)
        if not license_model:
            raise ValueError(Constants.ERROR_INVALID_LICENSE)

        new_customer = await self.customer_repo.get(new_customer_id)
        if not new_customer:
            raise ValueError("New customer not found")

        # Deactivate all existing machines
        machines = await self.machine_repo.get_machines_by_license(license_model.id)
        for machine in machines:
            await self.machine_repo.update(
                machine.id,
                status=MachineStatus.REPLACED,
                deactivated_at=datetime.utcnow(),
            )

        # Update license to new customer
        await self.license_repo.update(
            license_model.id,
            customer_id=new_customer_id,
            customer_name=new_customer.name,
            customer_email=new_customer.email,
            status=ActivationStatus.PENDING,
        )

        logger.info(
            "License transferred: {key} to {customer}",
            key=license_key[:16] + "...",
            customer=new_customer.name,
        )

        return True