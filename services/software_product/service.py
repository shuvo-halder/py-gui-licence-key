"""
SoftwareProduct service implementation.

This module provides the business logic layer for managing registered
software products, including CRUD operations and client SDK generation.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.software_product import SoftwareProductModel
from database.repository.software_product_repository import SoftwareProductRepository
from services.encryption.service import EncryptionService
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class SoftwareProductService:
    """Business logic service for software product management."""

    def __init__(
        self,
        session: AsyncSession,
        encryption_service: Optional[EncryptionService] = None,
    ) -> None:
        """
        Initialize the service.

        Args:
            session: Async SQLAlchemy session.
            encryption_service: Optional encryption service for key generation.
        """
        self.session = session
        self.repository = SoftwareProductRepository(session)
        self.encryption = encryption_service or EncryptionService()

    async def create_product(
        self,
        name: str,
        version: str,
        validation_type: str = "online",
        exe_name: Optional[str] = None,
        company_name: Optional[str] = None,
        machine_lock: bool = True,
        max_activations: int = 5,
        anti_tamper: bool = True,
        clock_protection: bool = True,
        feature_flags: Optional[str] = None,
    ) -> SoftwareProductModel:
        """
        Create a new software product registration.

        Args:
            name: Software name.
            version: Software version string.
            validation_type: License validation mode (online, offline, hybrid).
            exe_name: Executable filename for anti-tamper.
            company_name: Company/developer name.
            machine_lock: Whether to lock licenses to machines.
            max_activations: Maximum concurrent activations.
            anti_tamper: Enable anti-tamper executable validation.
            clock_protection: Enable clock manipulation detection.
            feature_flags: JSON string of enabled feature flags.

        Returns:
            The created SoftwareProductModel instance.

        Raises:
            ValueError: If a product with the same name already exists.
        """
        existing = await self.repository.get_by_name(name)
        if existing:
            raise ValueError(f"Software product '{name}' already exists")

        product = await self.repository.create(
            app_id=str(uuid.uuid4()),
            name=name,
            version=version,
            validation_type=validation_type,
            exe_name=exe_name,
            company_name=company_name,
            machine_lock=machine_lock,
            max_activations=max_activations,
            anti_tamper=anti_tamper,
            clock_protection=clock_protection,
            feature_flags=feature_flags,
            is_active=True,
            is_deleted=False,
        )

        logger.info(f"Created software product: {name} (app_id={product.app_id})")
        return product

    async def get_product(self, product_id: str) -> Optional[SoftwareProductModel]:
        """Get a software product by its database ID."""
        return await self.repository.get(product_id)

    async def get_product_by_app_id(
        self, app_id: str
    ) -> Optional[SoftwareProductModel]:
        """Get a software product by its application UUID."""
        return await self.repository.get_by_app_id(app_id)

    async def update_product(
        self,
        product_id: str,
        **kwargs: Any,
    ) -> Optional[SoftwareProductModel]:
        """
        Update a software product's fields.

        Args:
            product_id: The database ID of the product.
            **kwargs: Fields to update.

        Returns:
            The updated product or None if not found.
        """
        allowed_fields = {
            "name", "version", "exe_name", "company_name",
            "validation_type", "machine_lock", "max_activations",
            "anti_tamper", "clock_protection", "feature_flags",
            "is_active",
        }
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        update_data["updated_at"] = datetime.utcnow()

        product = await self.repository.update(product_id, **update_data)
        if product:
            logger.info(f"Updated software product: {product.name}")
        return product

    async def delete_product(self, product_id: str) -> bool:
        """Soft-delete a software product."""
        result = await self.repository.delete(product_id, soft=True)
        if result:
            logger.info(f"Deleted software product: {product_id}")
        return result

    async def list_products(
        self, skip: int = 0, limit: int = 100
    ) -> list[SoftwareProductModel]:
        """List all active software products."""
        return await self.repository.get_active_products(skip=skip, limit=limit)

    async def search_products(
        self, search_term: str, skip: int = 0, limit: int = 100
    ) -> list[SoftwareProductModel]:
        """Search software products."""
        return await self.repository.search_products(search_term, skip, limit)

    async def count_products(self) -> int:
        """Count all active software products."""
        return await self.repository.count({"is_deleted": False})

    async def generate_client_sdk(
        self, product_id: str, output_dir: Optional[str] = None
    ) -> str:
        """
        Generate a client integration SDK package for a software product.

        Creates a zip file containing the client SDK with license validation,
        machine fingerprinting, configuration, and documentation.

        Args:
            product_id: The database ID of the software product.
            output_dir: Directory to output the SDK package. Defaults to ./exports.

        Returns:
            Path to the generated SDK zip file.

        Raises:
            ValueError: If the product is not found.
        """
        product = await self.repository.get(product_id)
        if not product:
            raise ValueError(f"Software product not found: {product_id}")

        output_dir = output_dir or os.path.join(settings.BACKUP_DIR, "client_sdk")
        sdk_dir = os.path.join(output_dir, f"client_sdk_{product.app_id}")
        os.makedirs(sdk_dir, exist_ok=True)

        # Export RSA public key
        public_key_path = os.path.join(sdk_dir, "public.pem")
        pub_key = self.encryption.get_public_key_pem()
        with open(public_key_path, "w") as f:
            f.write(pub_key)

        # Generate config.json
        config = {
            "app_id": product.app_id,
            "app_name": product.name,
            "version": product.version,
            "company_name": product.company_name or "",
            "validation_type": product.validation_type,
            "machine_lock": product.machine_lock,
            "max_activations": product.max_activations,
            "anti_tamper": product.anti_tamper,
            "clock_protection": product.clock_protection,
            "api_url": settings.get_api_url(),
            "api_version": "v1",
            "feature_flags": json.loads(product.feature_flags) if product.feature_flags else [],
        }
        config_path = os.path.join(sdk_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Generate SDK files
        self._write_license_client(sdk_dir, product, config)
        self._write_validator(sdk_dir, product, config)
        self._write_machine_fingerprint(sdk_dir, product)
        self._write_readme(sdk_dir, product, config)
        self._write_init_file(sdk_dir, product)

        # Create zip archive
        zip_path = shutil.make_archive(
            base_name=str(Path(sdk_dir)),
            format="zip",
            root_dir=output_dir,
            base_dir=f"client_sdk_{product.app_id}",
        )

        logger.info(
            f"Generated client SDK for {product.name}: {zip_path}"
        )
        return zip_path

    def _write_init_file(
        self, sdk_dir: str, product: SoftwareProductModel
    ) -> None:
        """Write __init__.py for the SDK package."""
        content = f'''"""
{product.name} - License Client SDK

Auto-generated SDK for {product.name} v{product.version}.
Do not modify this file directly.
"""

from .license_client import LicenseClient
from .validator import LicenseValidator
from .machine_fingerprint import MachineFingerprint

__all__ = [
    "LicenseClient",
    "LicenseValidator",
    "MachineFingerprint",
]
'''
        with open(os.path.join(sdk_dir, "__init__.py"), "w") as f:
            f.write(content)

    def _write_license_client(
        self,
        sdk_dir: str,
        product: SoftwareProductModel,
        config: dict,
    ) -> None:
        """Write license_client.py SDK file."""
        content = f'''"""
License Client for {product.name}.

This module handles communication with the license server for
activation, validation, and deactivation of licenses.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone

import requests


class LicenseClient:
    """
    Client for communicating with the license server API.

    Handles license activation, validation, and deactivation
    for {product.name} v{product.version}.
    """

    def __init__(
        self,
        app_id: str = "{product.app_id}",
        api_url: str = "{config['api_url']}",
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the license client.

        Args:
            app_id: The application UUID.
            api_url: URL of the license server API.
            config_path: Path to config.json (auto-detected if None).
        """
        self.app_id = app_id
        self.api_url = api_url.rstrip("/")
        self.config_path = config_path or self._find_config()
        self._load_config()

    def _find_config(self) -> str:
        """Find the config.json file relative to this module."""
        module_dir = Path(__file__).parent.resolve()
        config_path = module_dir / "config.json"
        if config_path.exists():
            return str(config_path)
        # Fallback to current directory
        return "config.json"

    def _load_config(self) -> None:
        """Load configuration from config.json."""
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {{}}

    def activate(
        self, license_key: str, machine_fingerprint: str
    ) -> dict[str, Any]:
        """
        Activate a license with the server.

        Args:
            license_key: The license key to activate.
            machine_fingerprint: Hardware fingerprint of the machine.

        Returns:
            Server response with activation result.

        Raises:
            ConnectionError: If the server is unreachable.
            ValueError: If activation fails.
        """
        try:
            response = requests.post(
                f"{{self.api_url}}/api/v1/activate",
                json={{
                    "app_id": self.app_id,
                    "license_key": license_key,
                    "machine_fingerprint": machine_fingerprint,
                }},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Could not connect to license server at {{self.api_url}}: {{e}}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Activation request failed: {{e}}")

    def validate(
        self, license_key: str, machine_fingerprint: str
    ) -> dict[str, Any]:
        """
        Validate an activated license with the server.

        Args:
            license_key: The license key to validate.
            machine_fingerprint: Hardware fingerprint of the machine.

        Returns:
            Server response with validation result.
        """
        try:
            response = requests.post(
                f"{{self.api_url}}/api/v1/validate",
                json={{
                    "app_id": self.app_id,
                    "license_key": license_key,
                    "machine_fingerprint": machine_fingerprint,
                }},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {{
                "valid": False,
                "reason": "server_unreachable",
                "message": "License server is unavailable. "
                           "Check your internet connection.",
            }}

    def deactivate(
        self, license_key: str, machine_fingerprint: str
    ) -> dict[str, Any]:
        """
        Deactivate a license on the server.

        Args:
            license_key: The license key to deactivate.
            machine_fingerprint: Hardware fingerprint of the machine.
        """
        try:
            response = requests.post(
                f"{{self.api_url}}/api/v1/deactivate",
                json={{
                    "app_id": self.app_id,
                    "license_key": license_key,
                    "machine_fingerprint": machine_fingerprint,
                }},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Deactivation failed: {{e}}")
'''
        with open(os.path.join(sdk_dir, "license_client.py"), "w") as f:
            f.write(content)

    def _write_validator(
        self,
        sdk_dir: str,
        product: SoftwareProductModel,
        config: dict,
    ) -> None:
        """Write validator.py SDK file."""
        anti_tamper_enabled = "True" if product.anti_tamper else "False"
        clock_protection_enabled = "True" if product.clock_protection else "False"
        machine_lock_enabled = "True" if product.machine_lock else "False"
        validation_type = product.validation_type

        content = f'''"""
License Validator for {product.name}.

Handles startup license validation including signature verification,
expiration checking, machine fingerprint matching, anti-tampering,
and clock rollback detection.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

from .machine_fingerprint import MachineFingerprint


class LicenseValidator:
    """
    Validates licenses at application startup.

    Performs multi-layered validation including:
    - RSA signature verification
    - Expiration date checking
    - Machine fingerprint matching
    - Anti-tamper executable hash verification
    - Clock rollback detection
    - Online server validation (if configured)
    """

    ANTI_TAMPER: bool = {anti_tamper_enabled}
    CLOCK_PROTECTION: bool = {clock_protection_enabled}
    MACHINE_LOCK: bool = {machine_lock_enabled}
    VALIDATION_TYPE: str = "{validation_type}"

    def __init__(
        self,
        license_file: Optional[str] = None,
        public_key_file: Optional[str] = None,
        config_file: Optional[str] = None,
    ) -> None:
        """
        Initialize the license validator.

        Args:
            license_file: Path to the local license file.
            public_key_file: Path to the RSA public key PEM file.
            config_file: Path to config.json.
        """
        self.module_dir = Path(__file__).parent.resolve()
        self.license_file = license_file or str(
            self.module_dir / "license.lic"
        )
        self.public_key_file = public_key_file or str(
            self.module_dir / "public.pem"
        )
        self.config_file = config_file or str(
            self.module_dir / "config.json"
        )
        self.fingerprint = MachineFingerprint()
        self._config: dict[str, Any] = {{}}
        self._load_config()

    def _load_config(self) -> None:
        """Load SDK configuration."""
        try:
            with open(self.config_file, "r") as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {{}}

    def validate(self) -> dict[str, Any]:
        """
        Perform full license validation.

        Returns:
            Dictionary with 'valid' bool and 'message' string.
        """
        # Step 1: Load the local license file
        if not os.path.exists(self.license_file):
            return {{
                "valid": False,
                "message": "No license file found. Please activate the software.",
                "reason": "no_license_file",
            }}

        try:
            with open(self.license_file, "r") as f:
                license_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return {{
                "valid": False,
                "message": f"Invalid license file: {{e}}",
                "reason": "invalid_license_file",
            }}

        # Step 2: Verify RSA signature
        signature_valid = self._verify_signature(license_data)
        if not signature_valid:
            return {{
                "valid": False,
                "message": "License signature verification failed. "
                           "The license has been tampered with.",
                "reason": "invalid_signature",
            }}

        # Step 3: Validate expiration date
        expiration = license_data.get("expires_at")
        if expiration:
            try:
                expiry_date = datetime.fromisoformat(expiration)
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                if now > expiry_date:
                    return {{
                        "valid": False,
                        "message": "License has expired.",
                        "reason": "expired",
                        "expires_at": expiration,
                    }}
            except (ValueError, TypeError):
                pass

        # Step 4: Validate machine fingerprint
        if self.MACHINE_LOCK:
            stored_fingerprint = license_data.get("machine_fingerprint")
            if stored_fingerprint:
                current_fingerprint = self.fingerprint.generate()
                if stored_fingerprint != current_fingerprint:
                    return {{
                        "valid": False,
                        "message": "License is locked to a different machine.",
                        "reason": "machine_mismatch",
                    }}

        # Step 5: Anti-tamper check
        if self.ANTI_TAMPER:
            exe_hash = license_data.get("executable_hash")
            if exe_hash:
                current_hash = self._calculate_executable_hash()
                if current_hash and exe_hash != current_hash:
                    return {{
                        "valid": False,
                        "message": "Application executable has been modified.",
                        "reason": "tampered",
                    }}

        # Step 6: Clock rollback detection
        if self.CLOCK_PROTECTION:
            clock_valid = self._check_clock_rollback(license_data)
            if not clock_valid:
                return {{
                    "valid": False,
                    "message": "System clock manipulation detected.",
                    "reason": "clock_manipulated",
                }}

        # Step 7: Online validation (if configured)
        if self.VALIDATION_TYPE in ("online", "hybrid"):
            online_result = self._validate_online(license_data)
            if not online_result.get("valid", False):
                if self.VALIDATION_TYPE == "online":
                    return {{
                        "valid": False,
                        "message": online_result.get(
                            "message", "Online validation failed."
                        ),
                        "reason": "online_validation_failed",
                    }}
                # Hybrid mode: allow with warning
                return {{
                    "valid": True,
                    "message": "License validated (offline mode). "
                               "Online validation unavailable.",
                    "offline": True,
                }}

        return {{
            "valid": True,
            "message": "License validation successful.",
            "reason": "valid",
        }}

    def _verify_signature(self, license_data: dict) -> bool:
        """Verify the RSA signature of the license data."""
        try:
            with open(self.public_key_file, "rb") as f:
                public_key = serialization.load_pem_public_key(
                    f.read(), backend=default_backend()
                )

            signature_hex = license_data.get("signature", "")
            if not signature_hex:
                return False

            signature = bytes.fromhex(signature_hex)

            # Create the message that was signed (all fields except signature)
            message_data = {{
                k: v for k, v in license_data.items() if k != "signature"
            }}
            message = json.dumps(message_data, sort_keys=True).encode()

            if isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature,
                    message,
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True
            return False
        except Exception:
            return False

    def _calculate_executable_hash(self) -> Optional[str]:
        """Calculate SHA256 hash of the running executable."""
        try:
            exe_path = sys.executable
            if not os.path.exists(exe_path):
                return None
            sha256 = hashlib.sha256()
            with open(exe_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None

    def _check_clock_rollback(self, license_data: dict) -> bool:
        """Detect system clock rollback attempts."""
        last_check = license_data.get("last_validation_time")
        if not last_check:
            return True

        try:
            last_time = float(last_check)
            current_time = time.time()
            # Allow 5 minutes of clock drift
            if current_time < last_time - 300:
                return False
            return True
        except (ValueError, TypeError):
            return True

    def _validate_online(self, license_data: dict) -> dict:
        """Perform online validation with the license server."""
        try:
            import requests

            license_key = license_data.get("license_key", "")
            machine_fp = self.fingerprint.generate()
            api_url = self._config.get(
                "api_url", "http://localhost:8000"
            )

            response = requests.post(
                f"{{api_url}}/api/v1/validate",
                json={{
                    "app_id": self._config.get("app_id", ""),
                    "license_key": license_key,
                    "machine_fingerprint": machine_fp,
                }},
                timeout=15,
            )
            return response.json()
        except Exception:
            return {{
                "valid": False,
                "message": "Server unreachable",
            }}

    def save_license(self, license_data: dict) -> None:
        """
        Save license data to the local license file.

        Args:
            license_data: License data dictionary to persist.
        """
        license_dir = Path(self.license_file).parent
        license_dir.mkdir(parents=True, exist_ok=True)

        with open(self.license_file, "w") as f:
            json.dump(license_data, f, indent=2)

    def get_license_info(self) -> dict[str, Any]:
        """Read and return license file information."""
        try:
            with open(self.license_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {{}}
'''
        with open(os.path.join(sdk_dir, "validator.py"), "w") as f:
            f.write(content)

    def _write_machine_fingerprint(
        self, sdk_dir: str, product: SoftwareProductModel
    ) -> None:
        """Write machine_fingerprint.py SDK file."""
        content = f'''"""
Machine Fingerprint for {product.name}.

Generates a unique hardware-based fingerprint for locking
licenses to specific machines.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
from typing import Optional


class MachineFingerprint:
    """
    Generates a unique machine fingerprint using hardware identifiers.

    Combines multiple hardware attributes to create a device-specific
    identifier that is resistant to spoofing.
    """

    def __init__(self) -> None:
        """Initialize the fingerprint generator."""
        self.system = platform.system().lower()

    def generate(self) -> str:
        """
        Generate a unique machine fingerprint.

        Returns:
            SHA256 hash string representing the machine identity.
        """
        components = self._collect_components()
        raw = "|".join(components)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _collect_components(self) -> list[str]:
        """Collect hardware identifiers for fingerprinting."""
        components = [
            platform.node(),
            platform.processor(),
            platform.machine(),
        ]

        # Add MAC address
        mac = self._get_mac_address()
        if mac:
            components.append(mac)

        # Add CPU info
        cpu = self._get_cpu_info()
        if cpu:
            components.append(cpu)

        # Add disk serial
        disk = self._get_disk_serial()
        if disk:
            components.append(disk)

        # Add motherboard serial (Windows)
        mb = self._get_motherboard_serial()
        if mb:
            components.append(mb)

        return [c for c in components if c]

    def _get_mac_address(self) -> Optional[str]:
        """Get the primary MAC address."""
        try:
            import uuid
            return ":".join(
                format(b, "02x")
                for b in uuid.getnode().to_bytes(6, "big")
            )
        except Exception:
            return None

    def _get_cpu_info(self) -> Optional[str]:
        """Get CPU identifier."""
        try:
            if self.system == "linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "Serial" in line:
                            return line.split(":")[1].strip()
            elif self.system == "windows":
                output = subprocess.check_output(
                    ["wmic", "cpu", "get", "ProcessorId"],
                    shell=True,
                    text=True,
                )
                lines = output.strip().split("\\n")
                return lines[1].strip() if len(lines) > 1 else None
            elif self.system == "darwin":
                output = subprocess.check_output(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    text=True,
                )
                return output.strip()
        except Exception:
            return None
        return None

    def _get_disk_serial(self) -> Optional[str]:
        """Get the disk drive serial number."""
        try:
            if self.system == "linux":
                output = subprocess.check_output(
                    ["udevadm", "info", "--query=all", "--name=/dev/sda"],
                    text=True,
                )
                for line in output.split("\\n"):
                    if "ID_SERIAL_SHORT" in line:
                        return line.split("=")[1].strip()
            elif self.system == "windows":
                output = subprocess.check_output(
                    ["wmic", "diskdrive", "get", "SerialNumber"],
                    shell=True,
                    text=True,
                )
                lines = output.strip().split("\\n")
                return lines[1].strip() if len(lines) > 1 else None
            elif self.system == "darwin":
                output = subprocess.check_output(
                    ["system_profiler", "SPStorageDataType"],
                    text=True,
                )
                for line in output.split("\\n"):
                    if "Serial Number" in line:
                        return line.split(":")[1].strip()
        except Exception:
            return None
        return None

    def _get_motherboard_serial(self) -> Optional[str]:
        """Get motherboard serial number (Windows only)."""
        try:
            if self.system == "windows":
                output = subprocess.check_output(
                    ["wmic", "baseboard", "get", "SerialNumber"],
                    shell=True,
                    text=True,
                )
                lines = output.strip().split("\\n")
                return lines[1].strip() if len(lines) > 1 else None
        except Exception:
            return None
        return None
'''
        with open(os.path.join(sdk_dir, "machine_fingerprint.py"), "w") as f:
            f.write(content)

    def _write_readme(
        self,
        sdk_dir: str,
        product: SoftwareProductModel,
        config: dict,
    ) -> None:
        """Write README.md for the SDK package."""
        content = f"""# {product.name} - License Client SDK

Auto-generated integration package for **{product.name} v{product.version}**.

## Overview

This SDK provides license validation and activation for your software.
Integrate it into your application to enforce licensing policies.

## Files

| File | Description |
|------|-------------|
| `license_client.py` | HTTP client for license server API communication |
| `validator.py` | Startup license validation (signature, expiry, machine, anti-tamper) |
| `machine_fingerprint.py` | Hardware fingerprint generation |
| `public.pem` | RSA public key for signature verification |
| `config.json` | SDK configuration |
| `README.md` | This file |

## Quick Start

### 1. Copy SDK into Your Project

Copy the entire `client_sdk` folder into your project.

### 2. Basic Integration

```python
from client_sdk.validator import LicenseValidator
from client_sdk.license_client import LicenseClient

def main():
    validator = LicenseValidator()

    # Validate license at startup
    result = validator.validate()

    if not result["valid"]:
        print("License validation failed: {{result['message']}}")
        # Show activation dialog here
        return

    # Launch your application
    run_app()

if __name__ == "__main__":
    main()
```

### 3. Activation Flow (First Run)

```python
from client_sdk.license_client import LicenseClient
from client_sdk.machine_fingerprint import MachineFingerprint
from client_sdk.validator import LicenseValidator

fingerprint = MachineFingerprint()
client = LicenseClient()
validator = LicenseValidator()

# Generate machine fingerprint
machine_id = fingerprint.generate()

# Activate with license key
response = client.activate("YOUR-LICENSE-KEY", machine_id)

if response.get("activated"):
    # Save license locally
    validator.save_license(response["license_data"])
    print("Activation successful!")
else:
    print(f"Activation failed: {{response.get('message', 'Unknown error')}}")
```

## Validation Modes

- **Online**: Requires server connection for every validation
- **Offline**: Validates locally using RSA signatures
- **Hybrid**: Tries online first, falls back to offline

## Security Features

| Feature | Description |
|---------|-------------|
| RSA Signature | License files are signed with 4096-bit RSA keys |
| Machine Lock | Licenses can be locked to specific hardware |
| Anti-Tamper | Detects executable modification |
| Clock Protection | Detects system clock rollback |

## Configuration

Edit `config.json` to set:

- `api_url`: License server URL
- `validation_type`: online/offline/hybrid
- `machine_lock`: Enable/disable machine locking

## Requirements

```
pip install requests cryptography
```

## License

Generated by Software License Manager - {product.company_name or 'LicenseManager Inc.'}
"""
        with open(os.path.join(sdk_dir, "README.md"), "w") as f:
            f.write(content)

    async def to_dict(self, product: SoftwareProductModel) -> dict[str, Any]:
        """Convert a product model to a serializable dictionary."""
        return product.to_dict()