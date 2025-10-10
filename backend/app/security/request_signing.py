"""
Request signing with HMAC-SHA256 for financial operations.

Ensures integrity and prevents replay attacks for sensitive transactions.
"""
import hashlib
import hmac
import json
import time
import uuid
from typing import Any

from ..core.config import settings


class RequestSignature:
    """Service for signing and verifying financial operation requests."""

    SIGNATURE_TTL_SECONDS = 300  # 5 minutes
    ALGORITHM = "sha256"

    @staticmethod
    def generate_signature(
        method: str,
        endpoint: str,
        body: dict[str, Any] | str = "",
        timestamp: int | None = None,
        nonce: str | None = None,
    ) -> dict[str, str]:
        """
        Generate a request signature.

        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint path
            body: Request body (dict or JSON string)
            timestamp: Unix timestamp (defaults to now)
            nonce: Unique request identifier (generated if not provided)

        Returns:
            dict with signature, timestamp, and nonce
        """
        timestamp = timestamp or int(time.time())
        nonce = nonce or str(uuid.uuid4())

        # Normalize body
        body_str = json.dumps(body, sort_keys=True) if isinstance(body, dict) else body

        # Create signature payload
        payload = f"{method}\n{endpoint}\n{body_str}\n{timestamp}\n{nonce}"

        # Sign with HMAC-SHA256
        signature = hmac.new(
            settings.secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return {
            "signature": signature,
            "timestamp": str(timestamp),
            "nonce": nonce,
            "algorithm": RequestSignature.ALGORITHM,
        }

    @staticmethod
    def verify_signature(
        method: str,
        endpoint: str,
        signature: str,
        timestamp: str,
        nonce: str,
        body: dict[str, Any] | str = "",
    ) -> tuple[bool, str]:
        """
        Verify a request signature.

        Returns:
            tuple of (is_valid, message)
        """
        # Verify timestamp is recent
        try:
            req_timestamp = int(timestamp)
        except (ValueError, TypeError):
            return False, "Invalid timestamp format"

        current_time = int(time.time())
        if abs(current_time - req_timestamp) > RequestSignature.SIGNATURE_TTL_SECONDS:
            return False, "Request signature expired"

        # Regenerate signature and compare
        expected_sig_data = RequestSignature.generate_signature(
            method,
            endpoint,
            body,
            req_timestamp,
            nonce,
        )

        # Constant-time comparison to prevent timing attacks
        expected_sig = expected_sig_data["signature"]
        if not hmac.compare_digest(signature, expected_sig):
            return False, "Signature verification failed"

        return True, "Signature valid"

    @staticmethod
    def create_signed_request(
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a complete signed request for financial operations."""
        body = body or {}
        sig_data = RequestSignature.generate_signature(method, endpoint, body)

        return {
            "method": method,
            "endpoint": endpoint,
            "body": body,
            "headers": {
                "X-Signature": sig_data["signature"],
                "X-Timestamp": sig_data["timestamp"],
                "X-Nonce": sig_data["nonce"],
                "X-Algorithm": sig_data["algorithm"],
            },
        }
