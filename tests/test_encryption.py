"""
Tests for the encryption service.

Validates RSA key generation, signing, verification,
AES encryption/decryption, and hashing operations.
"""

from __future__ import annotations

import os
import tempfile
import pytest
from pathlib import Path

from services.encryption.service import EncryptionService


class TestEncryptionService:
    """Test suite for EncryptionService."""

    @pytest.fixture
    def encryption_service(self):
        """Create encryption service with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override keys directory
            service = EncryptionService(keys_dir=tmpdir)
            yield service

    def test_key_generation(self, encryption_service):
        """Test that RSA keys are generated properly."""
        assert encryption_service._private_key is not None
        assert encryption_service._public_key is not None
        assert encryption_service._fernet is not None

    def test_key_files_exist(self, encryption_service):
        """Test that key files are saved to disk."""
        assert encryption_service.private_key_path.exists()
        assert encryption_service.public_key_path.exists()
        assert encryption_service.aes_key_path.exists()

    def test_sign_and_verify(self, encryption_service):
        """Test digital signing and verification."""
        data = {"test": "data", "number": 42, "list": [1, 2, 3]}
        signature = encryption_service.sign_data(data)
        assert signature is not None
        assert len(signature) > 0

        # Verify valid signature
        assert encryption_service.verify_signature(data, signature) is True

        # Verify with tampered data
        tampered = {"test": "data", "number": 43, "list": [1, 2, 3]}
        assert encryption_service.verify_signature(tampered, signature) is False

    def test_license_signature_roundtrip(self, encryption_service):
        """Test license signature generation and verification."""
        license_data = {
            "license_key": "ABCD-1234-EFGH-5678",
            "license_type": "trial",
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "product_name": "Test Product",
            "expires_at": "2025-01-01T00:00:00",
            "features": ["reporting", "export"],
            "issued_at": "2024-01-01T00:00:00",
        }

        signature = encryption_service.generate_license_signature(license_data)
        assert signature is not None

        # Verify
        assert encryption_service.verify_license_signature(license_data, signature) is True

        # Tampered data should fail
        tampered = license_data.copy()
        tampered["customer_name"] = "Hacker"
        assert encryption_service.verify_license_signature(tampered, signature) is False

    def test_aes_encrypt_decrypt(self, encryption_service):
        """Test AES-256 encryption and decryption."""
        original = {"sensitive": "data", "key": "value", "nested": {"inner": "secret"}}

        encrypted = encryption_service.encrypt_data(original)
        assert encrypted is not None
        assert encrypted != str(original)

        decrypted = encryption_service.decrypt_data(encrypted)
        assert decrypted == original

    def test_license_file_encryption(self, encryption_service):
        """Test encrypting and decrypting license files."""
        license_data = {
            "license_key": "TEST-1234-5678-9012",
            "customer": "Test Corp",
        }

        with tempfile.NamedTemporaryFile(suffix=".lic", delete=False) as f:
            license_path = f.name

        try:
            encryption_service.encrypt_license_file(license_data, license_path)

            # Verify file exists and is encrypted
            assert os.path.exists(license_path)
            content = Path(license_path).read_text()
            assert "TEST-1234-5678-9012" not in content  # Should be encrypted

            # Decrypt and verify
            decrypted = encryption_service.decrypt_license_file(license_path)
            assert decrypted == license_data

        finally:
            if os.path.exists(license_path):
                os.unlink(license_path)

    def test_hashing(self, encryption_service):
        """Test SHA-256 hashing."""
        data = "test_data"
        hash1 = encryption_service.hash_data(data)
        hash2 = encryption_service.hash_data(data)
        hash3 = encryption_service.hash_data("different")

        assert hash1 == hash2  # Same input -> same hash
        assert hash1 != hash3  # Different input -> different hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    def test_hmac(self, encryption_service):
        """Test HMAC generation and verification."""
        data = "message"
        key = "secret_key"

        hmac_value = encryption_service.generate_hmac(data, key)
        assert encryption_service.verify_hmac(data, key, hmac_value) is True
        assert encryption_service.verify_hmac(data, "wrong_key", hmac_value) is False
        assert encryption_service.verify_hmac("wrong_msg", key, hmac_value) is False

    def test_key_fingerprint(self, encryption_service):
        """Test public key fingerprint."""
        fingerprint = encryption_service.get_key_fingerprint()
        assert fingerprint is not None
        assert len(fingerprint) == 64  # SHA-256 hash

    def test_public_key_pem(self, encryption_service):
        """Test public key export."""
        pem = encryption_service.get_public_key_pem()
        assert pem.startswith("-----BEGIN PUBLIC KEY-----")
        assert pem.endswith("-----END PUBLIC KEY-----\n")

    def test_key_rotation(self, encryption_service):
        """Test key rotation."""
        old_fingerprint = encryption_service.get_key_fingerprint()
        result = encryption_service.rotate_keys()

        assert result["old_fingerprint"] == old_fingerprint
        assert result["new_fingerprint"] != old_fingerprint