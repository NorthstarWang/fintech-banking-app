"""
Mock model classes that mimic SQLAlchemy models for the mock data system.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

class BaseMockModel:
    """Base class for all mock models."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class User(BaseMockModel):
    """Mock User model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.full_name = kwargs.get('full_name')
        self.hashed_password = kwargs.get('hashed_password')
        self.is_active = kwargs.get('is_active', True)
        self.is_admin = kwargs.get('is_admin', False)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Account(BaseMockModel):
    """Mock Account model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.account_number = kwargs.get('account_number')
        self.account_type = kwargs.get('account_type')
        self.balance = kwargs.get('balance', 0.0)
        self.currency = kwargs.get('currency', 'USD')
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Transaction(BaseMockModel):
    """Mock Transaction model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.account_id = kwargs.get('account_id')
        self.user_id = kwargs.get('user_id')
        self.amount = kwargs.get('amount')
        self.transaction_type = kwargs.get('transaction_type')
        self.description = kwargs.get('description')
        self.category_id = kwargs.get('category_id')
        self.merchant_id = kwargs.get('merchant_id')
        self.date = kwargs.get('date', datetime.utcnow().isoformat())
        self.status = kwargs.get('status', 'completed')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Category(BaseMockModel):
    """Mock Category model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
        self.icon = kwargs.get('icon')
        self.color = kwargs.get('color')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Card(BaseMockModel):
    """Mock Card model (VirtualCard)."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.account_id = kwargs.get('account_id')
        self.card_number = kwargs.get('card_number')
        self.card_type = kwargs.get('card_type')
        self.card_name = kwargs.get('card_name')
        self.credit_limit = kwargs.get('credit_limit')
        self.current_balance = kwargs.get('current_balance', 0.0)
        self.status = kwargs.get('status', 'active')
        self.expiry_date = kwargs.get('expiry_date')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Budget(BaseMockModel):
    """Mock Budget model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.category_id = kwargs.get('category_id')
        self.amount = kwargs.get('amount')
        self.period = kwargs.get('period')
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Goal(BaseMockModel):
    """Mock Goal model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name')
        self.target_amount = kwargs.get('target_amount')
        self.current_amount = kwargs.get('current_amount', 0.0)
        self.deadline = kwargs.get('deadline')
        self.category = kwargs.get('category')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Notification(BaseMockModel):
    """Mock Notification model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.title = kwargs.get('title')
        self.message = kwargs.get('message')
        self.type = kwargs.get('type')
        self.is_read = kwargs.get('is_read', False)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Message(BaseMockModel):
    """Mock Message model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.sender_id = kwargs.get('sender_id')
        self.recipient_id = kwargs.get('recipient_id')
        self.content = kwargs.get('content')
        self.is_read = kwargs.get('is_read', False)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Bill(BaseMockModel):
    """Mock Bill model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name')
        self.amount = kwargs.get('amount')
        self.due_date = kwargs.get('due_date')
        self.status = kwargs.get('status', 'pending')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Subscription(BaseMockModel):
    """Mock Subscription model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name')
        self.amount = kwargs.get('amount')
        self.billing_cycle = kwargs.get('billing_cycle')
        self.next_billing_date = kwargs.get('next_billing_date')
        self.category = kwargs.get('category')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class CreditScore(BaseMockModel):
    """Mock CreditScore model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.score = kwargs.get('score')
        self.agency = kwargs.get('agency')
        self.report_date = kwargs.get('report_date')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class SocialConnection(BaseMockModel):
    """Mock SocialConnection model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.connection_id = kwargs.get('connection_id')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class P2PTransaction(BaseMockModel):
    """Mock P2PTransaction model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.sender_id = kwargs.get('sender_id')
        self.recipient_id = kwargs.get('recipient_id')
        self.amount = kwargs.get('amount')
        self.description = kwargs.get('description')
        self.status = kwargs.get('status', 'completed')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class InvestmentAccount(BaseMockModel):
    """Mock InvestmentAccount model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.account_name = kwargs.get('account_name')
        self.account_type = kwargs.get('account_type')
        self.balance = kwargs.get('balance', 0.0)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Holding(BaseMockModel):
    """Mock Holding model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.investment_account_id = kwargs.get('investment_account_id')
        self.symbol = kwargs.get('symbol')
        self.quantity = kwargs.get('quantity')
        self.purchase_price = kwargs.get('purchase_price')
        self.current_price = kwargs.get('current_price')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class Alert(BaseMockModel):
    """Mock Alert model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.type = kwargs.get('type')
        self.threshold = kwargs.get('threshold')
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class AnalyticsEvent(BaseMockModel):
    """Mock AnalyticsEvent model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.event_type = kwargs.get('event_type')
        self.event_data = kwargs.get('event_data', {})
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

# Alias for compatibility
VirtualCard = Card

# Additional models for compatibility
class BankLink(BaseMockModel):
    """Mock BankLink model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.institution_name = kwargs.get('institution_name')
        self.account_mask = kwargs.get('account_mask')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class PlaidAccount(BaseMockModel):
    """Mock PlaidAccount model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.bank_link_id = kwargs.get('bank_link_id')
        self.account_id = kwargs.get('account_id')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)

class TransactionsSyncStatus(BaseMockModel):
    """Mock TransactionsSyncStatus model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.bank_link_id = kwargs.get('bank_link_id')
        self.last_sync = kwargs.get('last_sync')
        self.status = kwargs.get('status', 'success')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        super().__init__(**kwargs)