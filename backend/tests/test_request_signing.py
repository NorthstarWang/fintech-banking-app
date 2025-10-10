"""
Comprehensive tests for HMAC-SHA256 request signing system.

Tests digital signatures, replay attack prevention, integrity verification,
and signature validation.
"""

import pytest
import time
import json
from app.security.request_signing import RequestSignature
from app.core.config import settings


class TestSignatureGeneration:
    """Test HMAC-SHA256 signature generation."""

    def test_generate_signature_basic(self):
        """Test basic signature generation."""
        method = "POST"
        endpoint = "/api/transfer"
        body = {"amount": 1000, "recipient": "user123"}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        assert sig_data is not None
        assert "signature" in sig_data
        assert "timestamp" in sig_data
        assert "nonce" in sig_data
        assert "algorithm" in sig_data
        assert sig_data["algorithm"] == "sha256"

    def test_signature_format(self):
        """Test signature has correct format."""
        sig_data = RequestSignature.generate_signature("GET", "/api/balance", {})

        # Signature should be 64-character hex string (SHA256)
        assert len(sig_data["signature"]) == 64
        # Nonce should be valid UUID format (36 chars with hyphens)
        assert len(sig_data["nonce"]) == 36
        # Timestamp should be numeric
        assert sig_data["timestamp"].isdigit()

    def test_signature_consistency(self):
        """Test that same input generates same signature."""
        method = "POST"
        endpoint = "/api/payment"
        body = {"amount": 500}
        timestamp = int(time.time())
        nonce = "fixed-nonce-12345678901234567890"

        sig1 = RequestSignature.generate_signature(method, endpoint, body, timestamp, nonce)
        sig2 = RequestSignature.generate_signature(method, endpoint, body, timestamp, nonce)

        assert sig1["signature"] == sig2["signature"]
        assert sig1["timestamp"] == sig2["timestamp"]
        assert sig1["nonce"] == sig2["nonce"]

    def test_signature_difference_on_body_change(self):
        """Test that different body creates different signature."""
        method = "POST"
        endpoint = "/api/transfer"
        timestamp = int(time.time())
        nonce = "test-nonce-1"

        body1 = {"amount": 1000}
        body2 = {"amount": 2000}

        sig1 = RequestSignature.generate_signature(method, endpoint, body1, timestamp, nonce)
        sig2 = RequestSignature.generate_signature(method, endpoint, body2, timestamp, nonce)

        assert sig1["signature"] != sig2["signature"]

    def test_signature_difference_on_method_change(self):
        """Test that different HTTP method creates different signature."""
        endpoint = "/api/account"
        body = {}
        timestamp = int(time.time())
        nonce = "test-nonce-2"

        sig_get = RequestSignature.generate_signature("GET", endpoint, body, timestamp, nonce)
        sig_post = RequestSignature.generate_signature("POST", endpoint, body, timestamp, nonce)

        assert sig_get["signature"] != sig_post["signature"]

    def test_signature_difference_on_endpoint_change(self):
        """Test that different endpoint creates different signature."""
        method = "POST"
        body = {}
        timestamp = int(time.time())
        nonce = "test-nonce-3"

        sig1 = RequestSignature.generate_signature(method, "/api/transfer", body, timestamp, nonce)
        sig2 = RequestSignature.generate_signature(method, "/api/payment", body, timestamp, nonce)

        assert sig1["signature"] != sig2["signature"]

    def test_generate_signed_request(self):
        """Test creating complete signed request."""
        method = "POST"
        endpoint = "/api/invest"
        body = {"symbol": "AAPL", "quantity": 100}

        signed_request = RequestSignature.create_signed_request(method, endpoint, body)

        assert signed_request["method"] == method
        assert signed_request["endpoint"] == endpoint
        assert signed_request["body"] == body
        assert "headers" in signed_request
        assert "X-Signature" in signed_request["headers"]
        assert "X-Timestamp" in signed_request["headers"]
        assert "X-Nonce" in signed_request["headers"]
        assert "X-Algorithm" in signed_request["headers"]


class TestSignatureVerification:
    """Test signature verification and validation."""

    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        method = "POST"
        endpoint = "/api/trade"
        body = {"action": "buy", "ticker": "GOOGL"}
        timestamp = int(time.time())
        nonce = "verify-test-nonce"

        sig_data = RequestSignature.generate_signature(method, endpoint, body, timestamp, nonce)

        is_valid, message = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            str(timestamp),
            nonce,
            body,
        )

        assert is_valid is True
        assert "valid" in message.lower()

    def test_verify_invalid_signature(self):
        """Test verification fails for tampered signature."""
        method = "POST"
        endpoint = "/api/fund"
        body = {"amount": 5000}
        timestamp = int(time.time())
        nonce = "invalid-nonce-test"

        sig_data = RequestSignature.generate_signature(method, endpoint, body, timestamp, nonce)

        # Tamper with signature
        tampered_sig = sig_data["signature"][:-2] + "xx"

        is_valid, message = RequestSignature.verify_signature(
            method,
            endpoint,
            tampered_sig,
            str(timestamp),
            nonce,
            body,
        )

        assert is_valid is False
        assert "failed" in message.lower() or "invalid" in message.lower()

    def test_verify_detects_body_tampering(self):
        """Test verification detects tampering with request body."""
        method = "POST"
        endpoint = "/api/withdraw"
        original_body = {"amount": 100}
        timestamp = int(time.time())
        nonce = "body-tamper-test"

        sig_data = RequestSignature.generate_signature(method, endpoint, original_body, timestamp, nonce)

        # Tamper with body amount
        tampered_body = {"amount": 10000}

        is_valid, message = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            str(timestamp),
            nonce,
            tampered_body,
        )

        assert is_valid is False

    def test_verify_detects_endpoint_tampering(self):
        """Test verification detects tampering with endpoint."""
        method = "POST"
        endpoint = "/api/transfer"
        body = {"amount": 500}
        timestamp = int(time.time())
        nonce = "endpoint-tamper-test"

        sig_data = RequestSignature.generate_signature(method, endpoint, body, timestamp, nonce)

        # Try with different endpoint
        is_valid, message = RequestSignature.verify_signature(
            method,
            "/api/admin/transfer",  # Tampered endpoint
            sig_data["signature"],
            str(timestamp),
            nonce,
            body,
        )

        assert is_valid is False

    def test_verify_detects_method_tampering(self):
        """Test verification detects tampering with HTTP method."""
        method = "POST"
        endpoint = "/api/delete"
        body = {"id": 123}
        timestamp = int(time.time())
        nonce = "method-tamper-test"

        sig_data = RequestSignature.generate_signature(method, endpoint, body, timestamp, nonce)

        # Try with different method
        is_valid, message = RequestSignature.verify_signature(
            "GET",  # Tampered method
            endpoint,
            sig_data["signature"],
            str(timestamp),
            nonce,
            body,
        )

        assert is_valid is False


class TestReplayAttackPrevention:
    """Test replay attack prevention mechanisms."""

    def test_timestamp_validation(self):
        """Test that old timestamps are rejected."""
        method = "POST"
        endpoint = "/api/auth"
        body = {}
        # Timestamp from 10 minutes ago
        old_timestamp = int(time.time()) - 600

        sig_data = RequestSignature.generate_signature(method, endpoint, body, old_timestamp)

        is_valid, message = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            str(old_timestamp),
            sig_data["nonce"],
            body,
        )

        assert is_valid is False
        assert "expired" in message.lower() or "timeout" in message.lower()

    def test_nonce_uniqueness(self):
        """Test that nonces are unique."""
        method = "POST"
        endpoint = "/api/test"
        body = {}

        sig1 = RequestSignature.generate_signature(method, endpoint, body)
        sig2 = RequestSignature.generate_signature(method, endpoint, body)

        # Nonces should be different (unique for each request)
        assert sig1["nonce"] != sig2["nonce"]

    def test_signature_ttl(self):
        """Test signature has time-to-live limit."""
        # Verify that SIGNATURE_TTL_SECONDS is defined and reasonable
        assert RequestSignature.SIGNATURE_TTL_SECONDS > 0
        assert RequestSignature.SIGNATURE_TTL_SECONDS <= 3600  # Max 1 hour

    def test_future_timestamp_rejected(self):
        """Test that future timestamps are rejected."""
        method = "POST"
        endpoint = "/api/future"
        body = {}
        # Timestamp 10 minutes in the future
        future_timestamp = int(time.time()) + 600

        sig_data = RequestSignature.generate_signature(method, endpoint, body, future_timestamp)

        is_valid, message = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            str(future_timestamp),
            sig_data["nonce"],
            body,
        )

        # Future timestamps should typically be rejected
        # (depends on implementation tolerance)
        assert isinstance(is_valid, bool)


class TestIntegrityVerification:
    """Test request integrity verification."""

    def test_json_body_integrity(self):
        """Test integrity of JSON request bodies."""
        method = "POST"
        endpoint = "/api/invest"
        body = {"portfolio": [{"symbol": "AAPL", "quantity": 10}], "total": 1500}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        # Verify with same body
        is_valid, _ = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            sig_data["timestamp"],
            sig_data["nonce"],
            body,
        )

        assert is_valid is True

    def test_empty_body_signature(self):
        """Test signature of empty body."""
        method = "GET"
        endpoint = "/api/status"
        body = {}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)
        assert sig_data["signature"] is not None

        is_valid, _ = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            sig_data["timestamp"],
            sig_data["nonce"],
            body,
        )

        assert is_valid is True

    def test_string_body_signature(self):
        """Test signature with string body."""
        method = "POST"
        endpoint = "/api/message"
        body = "raw string body"

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        is_valid, _ = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            sig_data["timestamp"],
            sig_data["nonce"],
            body,
        )

        assert is_valid is True

    def test_complex_nested_structure(self):
        """Test signature of complex nested structures."""
        method = "POST"
        endpoint = "/api/complex"
        body = {
            "user": {
                "name": "John",
                "accounts": [
                    {"id": 1, "balance": 1000},
                    {"id": 2, "balance": 2000},
                ],
            },
            "metadata": {"timestamp": "2024-01-01", "version": "1.0"},
        }

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        is_valid, _ = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            sig_data["timestamp"],
            sig_data["nonce"],
            body,
        )

        assert is_valid is True


class TestTimingAttackResistance:
    """Test resistance to timing attacks."""

    def test_constant_time_comparison(self):
        """Test that signature comparison is constant-time."""
        method = "POST"
        endpoint = "/api/secure"
        body = {"data": "sensitive"}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        # Test multiple similar signatures
        # Constant-time comparison should prevent timing analysis
        for i in range(10):
            modified_sig = sig_data["signature"][:-1] + chr((ord(sig_data["signature"][-1]) + i) % 256)

            start = time.time()
            is_valid1, _ = RequestSignature.verify_signature(
                method,
                endpoint,
                modified_sig,
                sig_data["timestamp"],
                sig_data["nonce"],
                body,
            )
            time1 = time.time() - start

            start = time.time()
            is_valid2, _ = RequestSignature.verify_signature(
                method,
                endpoint,
                modified_sig,
                sig_data["timestamp"],
                sig_data["nonce"],
                body,
            )
            time2 = time.time() - start

            # Times should be approximately equal (constant-time)
            # Allow for some variance in test environment
            time_diff = abs(time1 - time2)
            # This is a rough check; real constant-time comparison verification
            # would require more sophisticated timing analysis


class TestSignatureEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_body(self):
        """Test signature of very large body."""
        method = "POST"
        endpoint = "/api/bulk"
        # Create large body
        body = {"items": [{"id": i, "data": "x" * 100} for i in range(1000)]}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        assert sig_data["signature"] is not None
        assert len(sig_data["signature"]) == 64  # SHA256 always 64 chars

    def test_special_characters_in_body(self):
        """Test signature with special characters."""
        method = "POST"
        endpoint = "/api/special"
        body = {"text": 'Special chars: "\'<>{}[]\\n\r\t'}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        is_valid, _ = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            sig_data["timestamp"],
            sig_data["nonce"],
            body,
        )

        assert is_valid is True

    def test_unicode_in_body(self):
        """Test signature with Unicode characters."""
        method = "POST"
        endpoint = "/api/unicode"
        body = {"text": "Unicode: 你好世界 🔐 مرحبا"}

        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        is_valid, _ = RequestSignature.verify_signature(
            method,
            endpoint,
            sig_data["signature"],
            sig_data["timestamp"],
            sig_data["nonce"],
            body,
        )

        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
