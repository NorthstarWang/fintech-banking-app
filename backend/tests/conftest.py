"""
Test configuration and fixtures for banking application tests
"""

import pytest
from fastapi.testclient import TestClient
import httpx
from typing import Dict, Any, Generator
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main app and memory-based data manager
from app.main_banking import app
from app.repositories.data_manager import data_manager
from app.storage import db

@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app"""
    # Reset memory data before each test for clean state
    data_manager.reset(seed=42)
    
    # Create test client - TestClient expects app as first positional argument
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    
    # Clean up after test
    data_manager.reset()


@pytest.fixture(scope="function")
def auth_headers(client: TestClient) -> Dict[str, str]:
    """Get authentication headers for a regular user"""
    response = client.post("/api/auth/login", json={
        "username": "john_doe",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client: TestClient) -> Dict[str, str]:
    """Get authentication headers for an admin user"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, Any]:
    """Sample user data for testing"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }


@pytest.fixture(scope="function")
def test_transaction_data() -> Dict[str, Any]:
    """Sample transaction data for testing"""
    return {
        "amount": 50.00,
        "description": "Test transaction",
        "category_id": 1,
        "merchant": "Test Store",
        "transaction_type": "expense"
    }


@pytest.fixture(scope="function")
def test_account_data() -> Dict[str, Any]:
    """Sample account data for testing"""
    return {
        "account_name": "Test Checking",
        "account_type": "checking",
        "balance": 1000.00,
        "currency": "USD",
        "is_active": True
    }


@pytest.fixture(scope="function")
def test_budget_data() -> Dict[str, Any]:
    """Sample budget data for testing"""
    return {
        "category_id": 1,
        "amount": 500.00,
        "period": "monthly",
        "start_date": "2025-06-01",
        "end_date": "2025-06-30"
    }


@pytest.fixture(scope="function")
def test_card_data() -> Dict[str, Any]:
    """Sample card data for testing"""
    return {
        "card_number": "4111111111111111",
        "card_type": "credit",
        "card_name": "Test Card",
        "credit_limit": 5000.00,
        "current_balance": 1000.00,
        "billing_cycle_day": 15
    }