"""
Encryption service implementing RSA-4096, AES-256, and SHA-256.

This service handles:
- RSA key pair generation and management
- Digital signing and verification of licenses
- AES-256 encryption/decryption of local license files
- SHA-256 hashing for integrity checks
- Secure key storage and management
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import settings
from core.constants import Constants
from core.logger import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """
    Enterprise-grade encryption service.

    Provides RSA-4096 signing, AES-256 encryption, and SHA-256 hashing
    for secure license management and data protection.
    """

    def __init__(self, keys_dir: Optional[str] = None) -> None:
        """
        Initialize the encryption service.

        Args:
            keys_dir: Directory for storing encryption keys.
                     Defaults to settings.LICENSE_DIR/keys.
        """
        self.keys_dir = Path(keys_dir or os.path.join(settings.LICENSE_DIR, "keys"))
        self.keys_dir.mkdir(parents=True, exist_ok=True)

        # Key file paths
        self.private_key_path = self.keys_dir / Constants.RSA_PRIVATE_KEY_FILE
        self.public_key_path = self.keys_dir / Constants.RSA_PUBLIC_KEY_FILE
        self.aes_key_path = self.keys_dir / Constants.AES_KEY_FILE

        # Load or generate keys
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None
        self._fernet: Optional[Fernet] = None

        self._initialize_keys()

    def _initialize_keys(self) -> None:
        """Initialize encryption keys, generating them if needed."""
        try:
            if self.private_key_path.exists() and self.public_key_path.exists():
                self._load_keys()
                logger.info("RSA keys loaded from disk")
            else:
                self._generate_rsa_keys()
                logger.info("New RSA keys generated")

            if self.aes_key_path.exists():
                self._load_aes_key()
            else:
                self._generate_aes_key()
                logger.info("New AES key generated")

        except Exception as e:
            logger.error(f"Failed to initialize encryption keys: {e}")
            raise

    def _generate_rsa_keys(self) -> None:
        """Generate RSA-4096 key pair."""
        try:
            # Generate private key
            self._private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=settings.RSA_KEY_SIZE,
            )
            self._public_key = self._private_key.public_key()

            # Save private key
            private_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    settings.SECRET_KEY.encode()
                ),
            )
            self.private_key_path.write_bytes(private_pem)
            self.private_key_path.chmod(0o600)  # Restrict permissions

            # Save public key
            public_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            self.public_key_path.write_bytes(public_pem)

        except Exception as e:
            logger.error(f"Failed to generate RSA keys: {e}")
            raise

    def _load_keys(self) -> None:
        """Load existing RSA keys from disk."""
        try:
            # Load private key
            private_pem = self.private_key_path.read_bytes()
            self._private_key = serialization.load_pem_private_key(
                private_pem,
                password=settings.SECRET_KEY.encode(),
            )

            # Load public key
            public_pem = self.public_key_path.read_bytes()
            self._public_key = serialization.load_pem_public_key(public_pem)

        except Exception as e:
            logger.error(f"Failed to load RSA keys: {e}")
            raise

    def _generate_aes_key(self) -> None:
        """Generate AES-256 key for Fernet symmetric encryption."""
        key = Fernet.generate_key()
        self.aes_key_path.write_bytes(key)
        self.aes_key_path.chmod(0o600)
        self._fernet = Fernet(key)

    def _load_aes_key(self) -> None:
        """Load existing AES key."""
        key = self.aes_key_path.read_bytes()
        self._fernet = Fernet(key)

    def sign_data(self, data: dict[str, Any]) -> str:
        """
        Digitally sign data using RSA-4096 private key.

        Args:
            data: Dictionary of data to sign.

        Returns:
            Base64-encoded digital signature.

        Raises:
            RuntimeError: If private key is not available.
        """
        if not self._private_key:
            raise RuntimeError("Private key not available for signing")

        try:
            # Serialize data to JSON
            data_json = json.dumps(data, sort_keys=True, default=str).encode()

            # Create signature
            signature = self._private_key.sign(
                data_json,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"Failed to sign data: {e}")
            raise

    def verify_signature(self, data: dict[str, Any], signature_b64: str) -> bool:
        """
        Verify RSA digital signature using public key.

        Args:
            data: Original data that was signed.
            signature_b64: Base64-encoded signature to verify.

        Returns:
            True if signature is valid, False otherwise.
        """
        if not self._public_key:
            logger.error("Public key not available for verification")
            return False

        try:
            data_json = json.dumps(data, sort_keys=True, default=str).encode()
            signature = base64.b64decode(signature_b64)

            self._public_key.verify(
                signature,
                data_json,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True

        except InvalidSignature:
            logger.warning("Invalid signature detected")
            return False
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def encrypt_data(self, data: dict[str, Any]) -> str:
        """
        Encrypt data using AES-256 (Fernet).

        Args:
            data: Dictionary of data to encrypt.

        Returns:
            Base64-encoded encrypted string.

        Raises:
            RuntimeError: If encryption key is not available.
        """
        if not self._fernet:
            raise RuntimeError("Encryption key not available")

        try:
            data_json = json.dumps(data, sort_keys=True, default=str)
            encrypted = self._fernet.encrypt(data_json.encode())
            return encrypted.decode()

        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> dict[str, Any]:
        """
        Decrypt AES-256 encrypted data.

        Args:
            encrypted_data: Base64-encoded encrypted string.

        Returns:
            Decrypted dictionary.

        Raises:
            RuntimeError: If decryption fails.
        """
        if not self._fernet:
            raise RuntimeError("Decryption key not available")

        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode())
            return json.loads(decrypted.decode())

        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise

    def hash_data(self, data: str) -> str:
        """
        Generate SHA-256 hash of data.

        Args:
            data: String data to hash.

        Returns:
            Hex-encoded SHA-256 hash.
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def hash_file(self, file_path: str) -> str:
        """
        Generate SHA-256 hash of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hex-encoded SHA-256 hash.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate_hmac(self, data: str, key: str) -> str:
        """
        Generate HMAC-SHA256 for data integrity.

        Args:
            data: Data to authenticate.
            key: Secret key for HMAC.

        Returns:
            Hex-encoded HMAC.
        """
        return hmac.new(
            key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

    def verify_hmac(self, data: str, key: str, hmac_value: str) -> bool:
        """
        Verify HMAC-SHA256.

        Args:
            data: Original data.
            key: Secret key used for HMAC.
            hmac_value: HMAC to verify.

        Returns:
            True if HMAC is valid, False otherwise.
        """
        expected = self.generate_hmac(data, key)
        return hmac.compare_digest(expected, hmac_value)

    def generate_license_signature(self, license_data: dict[str, Any]) -> str:
        """
        Generate a complete license signature including data hash.

        This combines data hashing with RSA signing for maximum security.

        Args:
            license_data: Complete license data including key, type, expiry, etc.

        Returns:
            Complete signature string.
        """
        # Create a canonical representation
        signature_data = {
            "license_key": license_data.get("license_key"),
            "license_type": license_data.get("license_type"),
            "customer_name": license_data.get("customer_name"),
            "customer_email": license_data.get("customer_email"),
            "product_name": license_data.get("product_name"),
            "expires_at": str(license_data.get("expires_at", "")),
            "features": sorted(license_data.get("features", [])),
            "issued_at": str(datetime.utcnow()),
        }

        return self.sign_data(signature_data)

    def verify_license_signature(
        self, license_data: dict[str, Any], signature: str
    ) -> bool:
        """
        Verify a license signature.

        Args:
            license_data: License data to verify.
            signature: Signature to verify against.

        Returns:
            True if signature is valid.
        """
        signature_data = {
            "license_key": license_data.get("license_key"),
            "license_type": license_data.get("license_type"),
            "customer_name": license_data.get("customer_name"),
            "customer_email": license_data.get("customer_email"),
            "product_name": license_data.get("product_name"),
            "expires_at": str(license_data.get("expires_at", "")),
            "features": sorted(license_data.get("features", [])),
            "issued_at": str(license_data.get("issued_at", "")),
        }

        return self.verify_signature(signature_data, signature)

    def encrypt_license_file(
        self, license_data: dict[str, Any], output_path: str
    ) -> None:
        """
        Encrypt and save license data to a file.

        Args:
            license_data: License data to encrypt.
            output_path: Path to save the encrypted license file.
        """
        encrypted = self.encrypt_data(license_data)
        Path(output_path).write_text(encrypted)
        logger.info(f"License file encrypted and saved: {output_path}")

    def decrypt_license_file(self, file_path: str) -> dict[str, Any]:
        """
        Decrypt a license file.

        Args:
            file_path: Path to the encrypted license file.

        Returns:
            Decrypted license data.
        """
        encrypted = Path(file_path).read_text()
        return self.decrypt_data(encrypted)

    def get_public_key_pem(self) -> str:
        """
        Get the public key in PEM format.

        Returns:
            Public key as PEM string.
        """
        if not self._public_key:
            raise RuntimeError("Public key not available")
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def get_key_fingerprint(self) -> str:
        """
        Get the SHA-256 fingerprint of the public key.

        Returns:
            Hex-encoded fingerprint.
        """
        pub_key_pem = self.get_public_key_pem()
        return self.hash_data(pub_key_pem)

    def rotate_keys(self) -> dict[str, str]:
        """
        Rotate encryption keys (generate new key pair).

        Returns:
            Dictionary with old and new key fingerprints.
        """
        old_fingerprint = self.get_key_fingerprint()

        # Generate new keys
        self._generate_rsa_keys()
        self._generate_aes_key()

        new_fingerprint = self.get_key_fingerprint()

        logger.info(
            "Encryption keys rotated: {old} -> {new}",
            old=old_fingerprint[:16],
            new=new_fingerprint[:16],
        )

        return {
            "old_fingerprint": old_fingerprint,
            "new_fingerprint": new_fingerprint,
        }