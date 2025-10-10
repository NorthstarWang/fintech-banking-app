"""
Authentication service for handling user authentication and sessions.
"""
from typing import Any

from app.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication-related operations."""

    def __init__(self, user_repository: UserRepository):
        """
        Initialize with user repository.

        Args:
            user_repository: Repository for user operations
        """
        self.user_repository = user_repository

    def register(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Register a new user.

        Args:
            user_data: User registration data

        Returns:
            Created user data

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        if self.user_repository.find_by_username(user_data.get('username', '')):
            raise ValueError("Username already exists")

        # Check if email exists
        if self.user_repository.find_by_email(user_data.get('email', '')):
            raise ValueError("Email already exists")

        # Create user
        return self.user_repository.create_user(user_data)


    def login(self, username: str, password: str, device_info: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Authenticate user and create session.

        Args:
            username: Username or email
            password: User password
            device_info: Optional device/browser information

        Returns:
            Dict with user data and session token

        Raises:
            ValueError: If credentials are invalid
        """
        # Try to find user by username or email
        user = self.user_repository.verify_password(username, password)

        if not user:
            # Try email if username failed
            email_user = self.user_repository.find_by_email(username)
            if email_user:
                user = self.user_repository.verify_password(email_user['username'], password)

        if not user:
            raise ValueError("Invalid credentials")

        # Check if user is active
        if not user.get('is_active', True):
            raise ValueError("Account is disabled")

        # Create session
        token = self.user_repository.create_session(user['id'], device_info)

        return {
            'user': user,
            'token': token
        }

    def logout(self, token: str) -> bool:
        """
        Logout user by invalidating session.

        Args:
            token: Session token

        Returns:
            True if logged out successfully
        """
        return self.user_repository.invalidate_session(token)

    def logout_all_sessions(self, user_id: str) -> int:
        """
        Logout user from all sessions.

        Args:
            user_id: User ID

        Returns:
            Number of sessions invalidated
        """
        return self.user_repository.invalidate_user_sessions(user_id)

    def get_current_user(self, token: str) -> dict[str, Any] | None:
        """
        Get current user from session token.

        Args:
            token: Session token

        Returns:
            User data if valid session, None otherwise
        """
        return self.user_repository.get_user_by_session(token)

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If current password is incorrect
        """
        # Get user
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not self.user_repository.verify_password(user['username'], current_password):
            raise ValueError("Current password is incorrect")

        # Update password
        success = self.user_repository.update_password(user_id, new_password)

        # Invalidate all sessions except current
        if success:
            self.user_repository.invalidate_user_sessions(user_id)

        return success

    def get_active_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        return self.user_repository.get_active_sessions(user_id)

    def validate_session(self, token: str) -> bool:
        """
        Validate if a session token is active and not expired.

        Args:
            token: Session token

        Returns:
            True if valid, False otherwise
        """
        user = self.user_repository.get_user_by_session(token)
        return user is not None
