"""
Hardware service for machine fingerprinting and identification.

This service creates unique hardware fingerprints using:
- CPU serial/ID
- Motherboard serial
- BIOS serial
- Disk serial
- MAC address
- Machine GUID

The fingerprint is hashed using SHA-256 and used for machine-locking licenses.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
import uuid
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)


class HardwareService:
    """
    Service for generating and managing hardware fingerprints.

    Creates unique machine identifiers by combining multiple hardware
    components and hashing them with SHA-256 for secure machine locking.
    """

    def __init__(self) -> None:
        """Initialize the hardware service."""
        self.system = platform.system().lower()
        self._fingerprint: Optional[str] = None

    def get_cpu_serial(self) -> Optional[str]:
        """
        Get CPU serial number.

        Returns:
            CPU serial or None if not available.
        """
        try:
            if self.system == "windows":
                cmd = "wmic cpu get processorid /value"
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL
                ).decode()
                for line in output.split("\n"):
                    if "ProcessorId" in line:
                        return line.split("=")[1].strip()
            elif self.system == "linux":
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "Serial" in line:
                            return line.split(":")[1].strip()
        except Exception as e:
            logger.debug(f"Failed to get CPU serial: {e}")
        return None

    def get_motherboard_serial(self) -> Optional[str]:
        """
        Get motherboard serial number.

        Returns:
            Motherboard serial or None if not available.
        """
        try:
            if self.system == "windows":
                cmd = "wmic baseboard get serialnumber /value"
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL
                ).decode()
                for line in output.split("\n"):
                    if "SerialNumber" in line:
                        return line.split("=")[1].strip()
        except Exception as e:
            logger.debug(f"Failed to get motherboard serial: {e}")
        return None

    def get_bios_serial(self) -> Optional[str]:
        """
        Get BIOS serial number.

        Returns:
            BIOS serial or None if not available.
        """
        try:
            if self.system == "windows":
                cmd = "wmic bios get serialnumber /value"
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL
                ).decode()
                for line in output.split("\n"):
                    if "SerialNumber" in line:
                        return line.split("=")[1].strip()
        except Exception as e:
            logger.debug(f"Failed to get BIOS serial: {e}")
        return None

    def get_disk_serial(self) -> Optional[str]:
        """
        Get primary disk serial number.

        Returns:
            Disk serial or None if not available.
        """
        try:
            if self.system == "windows":
                cmd = "wmic diskdrive get serialnumber /value"
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL
                ).decode()
                for line in output.split("\n"):
                    if "SerialNumber" in line:
                        return line.split("=")[1].strip()
        except Exception as e:
            logger.debug(f"Failed to get disk serial: {e}")
        return None

    def get_mac_address(self) -> Optional[str]:
        """
        Get primary MAC address.

        Returns:
            MAC address or None if not available.
        """
        try:
            import uuid as _uuid
            mac = _uuid.getnode()
            if (mac >> 40) % 2:
                return None
            return ":".join(f"{(mac >> elements) & 0xff:02x}" for elements in range(0, 8*6, 8)[::-1])
        except Exception as e:
            logger.debug(f"Failed to get MAC address: {e}")
        return None

    def get_machine_guid(self) -> Optional[str]:
        """
        Get machine GUID from system.

        Returns:
            Machine GUID or None if not available.
        """
        try:
            if self.system == "windows":
                cmd = "wmic csproduct get uuid /value"
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL
                ).decode()
                for line in output.split("\n"):
                    if "UUID" in line:
                        return line.split("=")[1].strip()
        except Exception as e:
            logger.debug(f"Failed to get machine GUID: {e}")
        return None

    def get_hostname(self) -> str:
        """
        Get system hostname.

        Returns:
            System hostname string.
        """
        return platform.node()

    def get_os_info(self) -> str:
        """
        Get operating system information.

        Returns:
            OS info string.
        """
        return f"{platform.system()} {platform.release()} {platform.version()}"

    def get_hardware_info(self) -> dict[str, Optional[str]]:
        """
        Get comprehensive hardware information.

        Returns:
            Dictionary of hardware identifiers.
        """
        return {
            "cpu_serial": self.get_cpu_serial(),
            "motherboard_serial": self.get_motherboard_serial(),
            "bios_serial": self.get_bios_serial(),
            "disk_serial": self.get_disk_serial(),
            "mac_address": self.get_mac_address(),
            "machine_guid": self.get_machine_guid(),
            "hostname": self.get_hostname(),
            "os_info": self.get_os_info(),
        }

    def generate_fingerprint(self) -> str:
        """
        Generate a unique hardware fingerprint.

        Combines multiple hardware identifiers and hashes them
        with SHA-256 to create a unique, reproducible fingerprint.

        Returns:
            SHA-256 hex digest of the hardware fingerprint.
        """
        hardware_info = self.get_hardware_info()

        # Build fingerprint string from available components
        fingerprint_parts = []
        for key, value in hardware_info.items():
            if value and key != "hostname" and key != "os_info":
                fingerprint_parts.append(f"{key}:{value}")

        # Add hostname and OS info for additional uniqueness
        fingerprint_parts.append(f"hostname:{self.get_hostname()}")
        fingerprint_parts.append(f"os:{self.get_os_info()}")

        # Sort for consistency
        fingerprint_parts.sort()

        # Join and hash
        fingerprint_string = "|".join(fingerprint_parts)
        fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()

        self._fingerprint = fingerprint
        logger.info("Hardware fingerprint generated")

        return fingerprint

    def get_fingerprint(self) -> str:
        """
        Get the cached hardware fingerprint, generating if needed.

        Returns:
            SHA-256 hardware fingerprint.
        """
        if not self._fingerprint:
            return self.generate_fingerprint()
        return self._fingerprint

    def verify_fingerprint(self, stored_fingerprint: str) -> bool:
        """
        Verify hardware fingerprint against stored fingerprint.

        Args:
            stored_fingerprint: Previously stored fingerprint to verify against.

        Returns:
            True if fingerprints match, False otherwise.
        """
        current = self.generate_fingerprint()
        match = current == stored_fingerprint

        if not match:
            logger.warning("Hardware fingerprint mismatch detected")
        else:
            logger.info("Hardware fingerprint verified successfully")

        return match

    def get_machine_name(self) -> str:
        """
        Get a user-friendly machine name.

        Returns:
            Machine name string.
        """
        return f"{self.get_hostname()}-{platform.machine()}"