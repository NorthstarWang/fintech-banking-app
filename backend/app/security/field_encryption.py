"""
Field-level encryption for PII using AES-256.

Encrypts sensitive fields like SSNs, account numbers, and tax IDs.
"""
import base64
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.config import settings


class FieldEncryption:
    """Service for encrypting and decrypting PII fields."""

    @staticmethod
    def _get_cipher() -> Fernet:
        """Get Fernet cipher instance."""
        # Derive key from secret_key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"bankflow-salt",  # Use static salt for consistent key derivation
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.secret_key.encode())
        )
        return Fernet(key)

    @staticmethod
    def encrypt_field(value: str) -> str:
        """
        Encrypt a sensitive field.

        Args:
            value: Plain text value to encrypt

        Returns:
            Encrypted value as base64 string
        """
        if not value:
            return ""

        cipher = FieldEncryption._get_cipher()
        encrypted = cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    @staticmethod
    def decrypt_field(encrypted_value: str) -> str:
        """
        Decrypt a sensitive field.

        Args:
            encrypted_value: Encrypted value as base64 string

        Returns:
            Plain text value
        """
        if not encrypted_value:
            return ""

        try:
            cipher = FieldEncryption._get_cipher()
            encrypted = base64.b64decode(encrypted_value.encode())
            decrypted = cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt field: {e!s}")

    @staticmethod
    def encrypt_ssn(ssn: str) -> str:
        """Encrypt SSN."""
        return FieldEncryption.encrypt_field(ssn)

    @staticmethod
    def decrypt_ssn(encrypted_ssn: str) -> str:
        """Decrypt SSN."""
        return FieldEncryption.decrypt_field(encrypted_ssn)

    @staticmethod
    def encrypt_account_number(account_number: str) -> str:
        """Encrypt account number."""
        return FieldEncryption.encrypt_field(account_number)

    @staticmethod
    def decrypt_account_number(encrypted_account: str) -> str:
        """Decrypt account number."""
        return FieldEncryption.decrypt_field(encrypted_account)

    @staticmethod
    def encrypt_tax_id(tax_id: str) -> str:
        """Encrypt tax ID (EIN or ITIN)."""
        return FieldEncryption.encrypt_field(tax_id)

    @staticmethod
    def decrypt_tax_id(encrypted_tax_id: str) -> str:
        """Decrypt tax ID."""
        return FieldEncryption.decrypt_field(encrypted_tax_id)

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Return SSN with only last 4 digits visible."""
        if len(ssn) < 4:
            return "***-***-****"
        return f"***-***-{ssn[-4:]}"

    @staticmethod
    def mask_account_number(account_number: str) -> str:
        """Return account number with only last 4 digits visible."""
        if len(account_number) < 4:
            return "*" * len(account_number)
        return "*" * (len(account_number) - 4) + account_number[-4:]

    @staticmethod
    def is_encrypted(value: str) -> bool:
        """Check if a value appears to be encrypted."""
        try:
            # Encrypted values are base64 encoded
            base64.b64decode(value, validate=True)
            # Additional check - encrypted values should be longer
            return len(value) > 20
        except Exception:
            return False

    @staticmethod
    def encrypt_dict(data: dict[str, Any], fields_to_encrypt: list[str] | None = None) -> dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing PII
            fields_to_encrypt: List of field names to encrypt. If None, encrypts all fields.

        Returns:
            Dictionary with specified fields encrypted
        """
        encrypted_data = data.copy()

        # If no fields specified, encrypt all fields
        if fields_to_encrypt is None:
            fields_to_encrypt = list(data.keys())

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                value = encrypted_data[field]
                # Handle nested dictionaries
                if isinstance(value, dict):
                    encrypted_data[field] = FieldEncryption.encrypt_dict(value)
                elif isinstance(value, str):
                    # Only encrypt string values
                    encrypted_data[field] = FieldEncryption.encrypt_field(value)
                # Note: Non-string types (int, float, bool) are not encrypted to preserve type info
        return encrypted_data

    @staticmethod
    def decrypt_dict(data: dict[str, Any], fields_to_decrypt: list[str] | None = None) -> dict[str, Any]:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary with encrypted fields
            fields_to_decrypt: List of field names to decrypt. If None, decrypts all fields.

        Returns:
            Dictionary with specified fields decrypted
        """
        decrypted_data = data.copy()

        # If no fields specified, decrypt all fields
        if fields_to_decrypt is None:
            fields_to_decrypt = list(data.keys())

        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                value = decrypted_data[field]
                # Handle nested dictionaries
                if isinstance(value, dict):
                    decrypted_data[field] = FieldEncryption.decrypt_dict(value)
                elif isinstance(value, str) and FieldEncryption.is_encrypted(value):
                    # Only decrypt if the value is actually encrypted (and a string)
                    decrypted_data[field] = FieldEncryption.decrypt_field(value)
                # Note: Non-string types (int, float, bool) pass through unchanged
        return decrypted_data
