"""JWT token management for authentication service."""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages JWT token generation and validation."""

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        token_expiry_hours: int = 24
    ):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=token_expiry_hours)

    def generate_token(self, user_id: int, username: str, **additional_claims) -> Dict[str, str]:
        """Generate a JWT token."""
        now = datetime.utcnow()
        expiry = now + self.token_expiry

        payload = {
            "user_id": user_id,
            "username": username,
            "iat": now,
            "exp": expiry,
            **additional_claims
        }

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )

        logger.info(f"Generated token for user {username}")

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": int(self.token_expiry.total_seconds()),
            "user_id": user_id
        }

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def get_token_expiry(self) -> int:
        """Get token expiry time in seconds."""
        return int(self.token_expiry.total_seconds())


# Global token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get or create the global token manager."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


def init_token_manager(
    secret_key: str = None,
    algorithm: str = "HS256",
    token_expiry_hours: int = 24
) -> TokenManager:
    """Initialize the global token manager."""
    global _token_manager
    _token_manager = TokenManager(secret_key, algorithm, token_expiry_hours)
    return _token_manager
