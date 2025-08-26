"""
Account repository for managing account data in the mock system.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.repositories.base_repository import BaseRepository

class AccountRepository(BaseRepository[Dict[str, Any]]):
    """Repository for managing account data."""
    
    def __init__(self, data_store: List[Dict[str, Any]]):
        super().__init__(data_store)
        
    def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new account.
        
        Args:
            account_data: Dictionary containing account details
            
        Returns:
            Created account dictionary
        """
        # Generate account number
        account_number = self._generate_account_number()
        account_data['account_number'] = account_number
        
        # Set defaults
        account_data.setdefault('balance', 0.0)
        account_data.setdefault('currency', 'USD')
        account_data.setdefault('is_active', True)
        
        return self.create(account_data)
        
    def _generate_account_number(self) -> str:
        """Generate a unique account number."""
        # Simple format: ACC + timestamp + random digits
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        random_part = str(uuid.uuid4().int)[:6]
        return f"ACC{timestamp}{random_part}"
        
    def find_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a user."""
        return self.find_by('user_id', user_id)
        
    def get_user_account_by_type(self, user_id: str, account_type: str) -> Optional[Dict[str, Any]]:
        """Get user's account by type."""
        accounts = self.find_by('user_id', user_id)
        for account in accounts:
            if account.get('account_type') == account_type:
                return account
        return None
        
    def update_balance(self, account_id: str, amount: float, operation: str = 'add') -> bool:
        """
        Update account balance.
        
        Args:
            account_id: Account ID
            amount: Amount to add/subtract
            operation: 'add' or 'subtract'
            
        Returns:
            True if successful
        """
        account = self.find_by_id(account_id)
        if not account:
            return False
            
        if operation == 'add':
            account['balance'] += amount
        elif operation == 'subtract':
            account['balance'] -= amount
            
        account['updated_at'] = datetime.utcnow().isoformat()
        return True
        
    def get_total_balance(self, user_id: str) -> Dict[str, Any]:
        """Get total balance across all user accounts."""
        accounts = self.find_by('user_id', user_id)
        
        total = 0.0
        by_type = {}
        
        for account in accounts:
            if account.get('is_active', True):
                balance = account.get('balance', 0.0)
                total += balance
                
                account_type = account.get('account_type', 'unknown')
                if account_type not in by_type:
                    by_type[account_type] = 0.0
                by_type[account_type] += balance
                
        return {
            'total': total,
            'by_type': by_type,
            'accounts_count': len(accounts)
        }
        
    def deactivate_account(self, account_id: str) -> bool:
        """Deactivate an account."""
        account = self.find_by_id(account_id)
        if not account:
            return False
            
        account['is_active'] = False
        account['updated_at'] = datetime.utcnow().isoformat()
        return True