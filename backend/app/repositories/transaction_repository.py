"""
Transaction repository for managing transaction data in the mock system.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.repositories.base_repository import BaseRepository

class TransactionRepository(BaseRepository[Dict[str, Any]]):
    """Repository for managing transaction data."""
    
    def __init__(self, data_store: List[Dict[str, Any]], categories: List[Dict[str, Any]]):
        super().__init__(data_store)
        self.categories = categories
        
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new transaction."""
        # Set defaults
        transaction_data.setdefault('status', 'completed')
        transaction_data.setdefault('date', datetime.utcnow().isoformat())
        
        return self.create(transaction_data)
        
    def get_user_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a user."""
        return self.find_by('user_id', user_id)
        
    def get_user_transactions_paginated(
        self, 
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        account_id: Optional[str] = None,
        category_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated transactions with filters."""
        # Start with user's transactions
        transactions = self.find_by('user_id', user_id)
        
        # Apply filters
        if account_id:
            transactions = [t for t in transactions if t.get('account_id') == account_id]
            
        if category_id:
            transactions = [t for t in transactions if t.get('category_id') == category_id]
            
        if start_date:
            transactions = [t for t in transactions if t.get('date', '') >= start_date]
            
        if end_date:
            transactions = [t for t in transactions if t.get('date', '') <= end_date]
            
        # Sort by date descending
        transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Add category info
        for trans in transactions:
            if trans.get('category_id'):
                trans['category'] = self.get_category(trans['category_id'])
        
        # Paginate
        total = len(transactions)
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            'items': transactions[start:end],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
        
    def get_recent_transactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for a user."""
        transactions = self.find_by('user_id', user_id)
        
        # Sort by date descending
        transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Add category info
        for trans in transactions[:limit]:
            if trans.get('category_id'):
                trans['category'] = self.get_category(trans['category_id'])
                
        return transactions[:limit]
        
    def get_transaction_summary(self, user_id: str, period: str = 'month') -> Dict[str, Any]:
        """Get transaction summary for a period."""
        transactions = self.find_by('user_id', user_id)
        
        # Calculate date range
        now = datetime.utcnow()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
            
        # Filter transactions by date
        period_transactions = [
            t for t in transactions 
            if datetime.fromisoformat(t.get('date', now.isoformat())) >= start_date
        ]
        
        # Calculate summary
        total_income = sum(
            t.get('amount', 0) for t in period_transactions 
            if t.get('transaction_type') == 'credit'
        )
        total_expense = sum(
            t.get('amount', 0) for t in period_transactions 
            if t.get('transaction_type') == 'debit'
        )
        
        return {
            'period': period,
            'total_income': total_income,
            'total_expense': total_expense,
            'net': total_income - total_expense,
            'transaction_count': len(period_transactions)
        }
        
    def get_spending_by_category(
        self, 
        user_id: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get spending breakdown by category."""
        transactions = self.find_by('user_id', user_id)
        
        # Filter by date if provided
        if start_date:
            transactions = [t for t in transactions if t.get('date', '') >= start_date]
        if end_date:
            transactions = [t for t in transactions if t.get('date', '') <= end_date]
            
        # Filter only expenses
        expenses = [t for t in transactions if t.get('transaction_type') == 'debit']
        
        # Group by category
        spending = {}
        for trans in expenses:
            category_id = trans.get('category_id')
            if category_id:
                if category_id not in spending:
                    category = self.get_category(category_id)
                    spending[category_id] = {
                        'category': category,
                        'amount': 0,
                        'count': 0
                    }
                spending[category_id]['amount'] += trans.get('amount', 0)
                spending[category_id]['count'] += 1
                
        return spending
        
    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category by ID."""
        for category in self.categories:
            if category.get('id') == category_id:
                return category
        return None
        
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        return self.categories