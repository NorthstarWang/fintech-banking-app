"""
Initialize proper test data for all tests.
"""
from app.repositories.data_manager import data_manager
import hashlib
from datetime import datetime
import uuid

def initialize_test_data():
    """Initialize comprehensive test data."""
    # Clear existing data
    data_manager.users = []
    data_manager.sessions = []
    data_manager.accounts = []
    data_manager.transactions = []
    
    # Create test users
    test_users = [
        {
            "id": "test-user-1",
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "hashed_password": hashlib.sha256("password123".encode()).hexdigest(),
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "test-user-2", 
            "username": "jane_smith",
            "email": "jane@example.com",
            "full_name": "Jane Smith",
            "hashed_password": hashlib.sha256("password123".encode()).hexdigest(),
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "admin-user",
            "username": "admin",
            "email": "admin@example.com", 
            "full_name": "Admin User",
            "hashed_password": hashlib.sha256("admin123".encode()).hexdigest(),
            "is_active": True,
            "is_admin": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    data_manager.users.extend(test_users)
    
    # Create test accounts
    test_accounts = [
        {
            "id": "1",
            "user_id": "test-user-1",
            "name": "Main Checking",
            "account_type": "checking",
            "account_number": "ACC001001",
            "balance": 1000.00,
            "currency": "USD",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "2",
            "user_id": "test-user-1",
            "name": "Savings Account",
            "account_type": "savings",
            "account_number": "ACC001002",
            "balance": 5000.00,
            "currency": "USD",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    data_manager.accounts.extend(test_accounts)
    
    print(f"Initialized {len(data_manager.users)} users and {len(data_manager.accounts)} accounts")

# Run initialization
initialize_test_data()
