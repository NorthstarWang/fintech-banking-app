"""
Pytest configuration and shared fixtures for all tests.

Provides common fixtures for:
- Dependency injection
- Database mocking
- Test data factories
- Async event loop
"""
import pytest
import asyncio
from typing import Dict, Any, Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_password() -> str:
    """Provide a valid test password."""
    return "SecurePass123!"


@pytest.fixture
def invalid_passwords() -> Dict[str, str]:
    """Provide invalid passwords for negative tests."""
    return {
        "too_short": "Short1!",
        "no_uppercase": "securepass123!",
        "no_lowercase": "SECUREPASS123!",
        "no_numbers": "SecurePass!",
        "no_special_chars": "SecurePass123",
        "empty": "",
        "whitespace": "   ",
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Provide sample user data for tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1-555-0123",
        "currency": "USD",
        "timezone": "UTC"
    }


@pytest.fixture
def multiple_users_data() -> list[Dict[str, Any]]:
    """Provide multiple test users."""
    return [
        {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "password": "SecurePass123!",
            "first_name": f"User{i}",
            "last_name": "Test",
            "phone": f"+1-555-000{i}",
            "currency": "USD",
            "timezone": "UTC"
        }
        for i in range(5)
    ]
