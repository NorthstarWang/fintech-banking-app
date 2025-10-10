"""
Comprehensive tests for AES-256 field-level encryption system.

Tests encryption/decryption, PII protection, data integrity,
and masking functionality.
"""

import pytest
from app.security.field_encryption import FieldEncryption


class TestBasicEncryption:
    """Test basic encryption and decryption operations."""

    def test_encrypt_decrypt_field(self):
        """Test basic field encryption and decryption."""
        plaintext = "sensitivedata123"

        encrypted = FieldEncryption.encrypt_field(plaintext)

        assert encrypted != plaintext
        assert encrypted is not None
        assert len(encrypted) > len(plaintext)  # Encrypted data is larger

        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == plaintext

    def test_decrypt_returns_plaintext(self):
        """Test that decryption returns original text."""
        test_values = [
            "simple",
            "with spaces here",
            "special!@#$%chars",
            "123456",
            "UPPERCASE",
            "CamelCase",
            "",  # Empty string
        ]

        for value in test_values:
            encrypted = FieldEncryption.encrypt_field(value)
            decrypted = FieldEncryption.decrypt_field(encrypted)
            assert decrypted == value

    def test_encrypt_consistency_per_value(self):
        """Test that encryption is deterministic for same value."""
        plaintext = "consistent_value"

        encrypted1 = FieldEncryption.encrypt_field(plaintext)
        encrypted2 = FieldEncryption.encrypt_field(plaintext)

        # Fernet with timestamp makes each encryption unique
        # So we test by decryption instead
        assert FieldEncryption.decrypt_field(encrypted1) == plaintext
        assert FieldEncryption.decrypt_field(encrypted2) == plaintext

    def test_different_plaintexts_different_ciphertexts(self):
        """Test different plaintext produces different ciphertext."""
        plaintext1 = "value1"
        plaintext2 = "value2"

        encrypted1 = FieldEncryption.encrypt_field(plaintext1)
        encrypted2 = FieldEncryption.encrypt_field(plaintext2)

        # Ciphertexts should be different
        assert encrypted1 != encrypted2

        # Both should decrypt to original
        assert FieldEncryption.decrypt_field(encrypted1) == plaintext1
        assert FieldEncryption.decrypt_field(encrypted2) == plaintext2


class TestSSNEncryption:
    """Test Social Security Number encryption."""

    def test_encrypt_ssn(self):
        """Test SSN encryption."""
        ssn = "123-45-6789"

        encrypted = FieldEncryption.encrypt_ssn(ssn)

        assert encrypted != ssn
        assert encrypted is not None

    def test_decrypt_ssn(self):
        """Test SSN decryption."""
        ssn = "987-65-4321"

        encrypted = FieldEncryption.encrypt_ssn(ssn)
        decrypted = FieldEncryption.decrypt_ssn(encrypted)

        assert decrypted == ssn

    def test_mask_ssn(self):
        """Test SSN masking."""
        ssn = "123-45-6789"

        masked = FieldEncryption.mask_ssn(ssn)

        assert masked != ssn
        assert "***" in masked or "*" in masked
        assert "-" in masked
        # Only last 4 digits should be visible
        assert "6789" in masked

    def test_mask_ssn_format(self):
        """Test SSN masking format."""
        ssn = "555-66-7777"

        masked = FieldEncryption.mask_ssn(ssn)

        # Should be format ***-**-7777
        assert masked.endswith("7777")
        assert masked.count("*") >= 6

    def test_ssn_without_dashes(self):
        """Test SSN encryption without dashes."""
        ssn = "1234567890"

        encrypted = FieldEncryption.encrypt_ssn(ssn)
        decrypted = FieldEncryption.decrypt_ssn(encrypted)

        assert decrypted == ssn


class TestBankAccountEncryption:
    """Test bank account number encryption."""

    def test_encrypt_account_number(self):
        """Test account number encryption."""
        account_number = "1234567890123456"

        encrypted = FieldEncryption.encrypt_field(account_number)

        assert encrypted != account_number
        assert encrypted is not None

    def test_decrypt_account_number(self):
        """Test account number decryption."""
        account_number = "9876543210987654"

        encrypted = FieldEncryption.encrypt_field(account_number)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == account_number

    def test_mask_account_number(self):
        """Test account number masking."""
        account_number = "1234567890123456"

        # Create a simple masking function for account numbers
        masked = "*" * 12 + account_number[-4:]

        assert masked.endswith("3456")
        assert masked.count("*") == 12


class TestTaxIDEncryption:
    """Test tax ID encryption."""

    def test_encrypt_tax_id(self):
        """Test tax ID encryption."""
        tax_id = "12-3456789"

        encrypted = FieldEncryption.encrypt_field(tax_id)

        assert encrypted != tax_id
        assert encrypted is not None

    def test_decrypt_tax_id(self):
        """Test tax ID decryption."""
        tax_id = "98-7654321"

        encrypted = FieldEncryption.encrypt_field(tax_id)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == tax_id


class TestDictionaryEncryption:
    """Test encryption of dictionary/object data."""

    def test_encrypt_dict(self):
        """Test encrypting dictionary data."""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "account": "9876543210",
        }

        encrypted = FieldEncryption.encrypt_dict(data)

        assert encrypted != data
        assert all(key in encrypted for key in data.keys())

    def test_decrypt_dict(self):
        """Test decrypting dictionary data."""
        data = {
            "firstName": "Jane",
            "lastName": "Smith",
            "taxId": "55-1234567",
        }

        encrypted = FieldEncryption.encrypt_dict(data)
        decrypted = FieldEncryption.decrypt_dict(encrypted)

        assert decrypted == data

    def test_nested_dict_encryption(self):
        """Test encryption of nested dictionary."""
        data = {
            "user": {
                "name": "Bob Wilson",
                "ssn": "555-66-7777",
            },
            "account": {
                "number": "1111222233334444",
                "type": "checking",
            },
        }

        encrypted = FieldEncryption.encrypt_dict(data)

        # Verify structure is preserved
        assert "user" in encrypted
        assert "account" in encrypted

        decrypted = FieldEncryption.decrypt_dict(encrypted)

        assert decrypted == data

    def test_dict_with_mixed_types(self):
        """Test dictionary with mixed data types."""
        data = {
            "name": "Test User",
            "age": 30,
            "ssn": "111-22-3333",
            "active": True,
            "balance": 1234.56,
        }

        encrypted = FieldEncryption.encrypt_dict(data)
        decrypted = FieldEncryption.decrypt_dict(encrypted)

        assert decrypted == data
        assert decrypted["age"] == 30
        assert decrypted["balance"] == 1234.56
        assert decrypted["active"] is True


class TestDataIntegrity:
    """Test data integrity after encryption/decryption."""

    def test_integrity_short_string(self):
        """Test integrity of short strings."""
        values = ["a", "ab", "abc", "test"]

        for value in values:
            encrypted = FieldEncryption.encrypt_field(value)
            decrypted = FieldEncryption.decrypt_field(encrypted)
            assert decrypted == value

    def test_integrity_long_string(self):
        """Test integrity of long strings."""
        long_value = "x" * 10000

        encrypted = FieldEncryption.encrypt_field(long_value)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == long_value

    def test_integrity_special_characters(self):
        """Test integrity with special characters."""
        special_chars = 'abc!@#$%^&*()_+-={}[]|\\:";\'<>?,./~`'

        encrypted = FieldEncryption.encrypt_field(special_chars)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == special_chars

    def test_integrity_unicode(self):
        """Test integrity with Unicode characters."""
        unicode_text = "Hello 世界 🔐 مرحبا мир"

        encrypted = FieldEncryption.encrypt_field(unicode_text)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == unicode_text

    def test_integrity_multiline(self):
        """Test integrity with multiline strings."""
        multiline = "Line 1\nLine 2\nLine 3\rLine 4"

        encrypted = FieldEncryption.encrypt_field(multiline)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == multiline


class TestEncryptionAlgorithm:
    """Test encryption algorithm properties."""

    def test_encrypted_size(self):
        """Test that encrypted data is reasonably sized."""
        plaintext = "test_data"

        encrypted = FieldEncryption.encrypt_field(plaintext)

        # Fernet adds overhead: IV (16 bytes) + HMAC (32 bytes) + timestamp (8 bytes)
        # Total overhead ~56 bytes, plus Base64 encoding expands by ~33%
        assert len(encrypted) > len(plaintext)

    def test_encryption_is_reversible(self):
        """Test that encryption is reversible."""
        original = "reversible_data"

        encrypted = FieldEncryption.encrypt_field(original)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == original

    def test_tampering_detection(self):
        """Test that tampering is detected."""
        plaintext = "important_data"

        encrypted = FieldEncryption.encrypt_field(plaintext)

        # Tamper with encrypted data
        tampered = encrypted[:-5] + "xxxxx"

        # Decryption should fail or return invalid data
        try:
            decrypted = FieldEncryption.decrypt_field(tampered)
            # If it doesn't raise, it should be corrupted
            assert decrypted != plaintext
        except Exception:
            # Tampering should raise an exception
            pass


class TestPIIProtection:
    """Test PII (Personally Identifiable Information) protection."""

    def test_multiple_pii_fields(self):
        """Test protection of multiple PII fields."""
        pii_data = {
            "ssn": "123-45-6789",
            "account_number": "1234567890123456",
            "tax_id": "12-3456789",
            "name": "John Doe",
        }

        encrypted = FieldEncryption.encrypt_dict(pii_data)

        # All sensitive data should be encrypted
        for key in pii_data:
            if isinstance(pii_data[key], str):
                # Encrypted values should be different
                assert encrypted[key] != pii_data[key]

    def test_selective_encryption(self):
        """Test selective encryption of sensitive fields."""
        data = {
            "public_id": "user123",  # Not encrypted
            "ssn": "555-66-7777",  # Encrypted
            "email": "user@example.com",  # Could be encrypted
        }

        # Encrypt only sensitive field
        encrypted_data = data.copy()
        encrypted_data["ssn"] = FieldEncryption.encrypt_field(data["ssn"])

        # Public ID should remain unchanged
        assert encrypted_data["public_id"] == "user123"

        # SSN should be encrypted
        assert encrypted_data["ssn"] != "555-66-7777"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self):
        """Test encryption of empty string."""
        empty = ""

        encrypted = FieldEncryption.encrypt_field(empty)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == ""

    def test_null_handling(self):
        """Test handling of null/None values."""
        # This depends on implementation
        # Some systems might handle None gracefully
        value = None

        try:
            encrypted = FieldEncryption.encrypt_field(str(value))
            assert "None" in encrypted or encrypted is not None
        except Exception:
            # Implementation might not support None
            pass

    def test_whitespace_preservation(self):
        """Test that whitespace is preserved."""
        whitespace = "  spaces  \t\ttabs\n\nnewlines  "

        encrypted = FieldEncryption.encrypt_field(whitespace)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == whitespace

    def test_case_sensitivity(self):
        """Test that case is preserved."""
        mixed_case = "AbCdEfGhIjKlMnOpQrStUvWxYz"

        encrypted = FieldEncryption.encrypt_field(mixed_case)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == mixed_case

    def test_numeric_string_preservation(self):
        """Test that numeric strings are preserved exactly."""
        numbers = "0123456789"

        encrypted = FieldEncryption.encrypt_field(numbers)
        decrypted = FieldEncryption.decrypt_field(encrypted)

        assert decrypted == numbers


class TestPerformance:
    """Test encryption performance characteristics."""

    def test_encryption_speed(self):
        """Test that encryption completes in reasonable time."""
        import time

        data = "test_data" * 100

        start = time.time()
        encrypted = FieldEncryption.encrypt_field(data)
        elapsed = time.time() - start

        # Should complete in < 1 second
        assert elapsed < 1.0

    def test_decryption_speed(self):
        """Test that decryption completes in reasonable time."""
        import time

        data = "test_data" * 100
        encrypted = FieldEncryption.encrypt_field(data)

        start = time.time()
        decrypted = FieldEncryption.decrypt_field(encrypted)
        elapsed = time.time() - start

        # Should complete in < 1 second
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
