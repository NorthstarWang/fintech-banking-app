"""
Base data classes and shared models used across the application.
These provide type safety and consistency between different layers.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

@dataclass
class UserData:
    """User data representation"""
    username: str
    email: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    currency: str = "USD"
    timezone: str = "UTC"
    is_active: bool = True
    last_login: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None

@dataclass
class AccountData:
    """Account data representation"""
    user_id: int
    name: str
    account_type: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    institution_name: Optional[str] = None
    balance: Decimal = Decimal("0.00")
    currency: str = "USD"
    is_active: bool = True
    credit_limit: Optional[Decimal] = None
    interest_rate: Optional[float] = None

@dataclass
class TransactionData:
    """Transaction data representation"""
    account_id: int
    amount: Decimal
    transaction_type: str
    transaction_date: datetime
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "completed"
    description: Optional[str] = None
    category_id: Optional[int] = None
    merchant_id: Optional[int] = None
    reference_number: Optional[str] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    location: Optional[str] = None
    receipt_url: Optional[str] = None

@dataclass
class CategoryData:
    """Category data representation"""
    name: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    icon: Optional[str] = "📁"
    color: Optional[str] = "#6B7280"
    is_income: bool = False
    is_system: bool = False
    user_id: Optional[int] = None
    parent_id: Optional[int] = None
    budget_amount: Optional[Decimal] = None

@dataclass
class BudgetData:
    """Budget data representation"""
    user_id: int
    category_id: int
    amount: Decimal
    period: str
    start_date: date
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    end_date: Optional[date] = None
    spent_amount: Decimal = Decimal("0.00")
    alert_threshold: float = 0.8
    alert_enabled: bool = True
    is_active: bool = True

@dataclass
class GoalData:
    """Financial goal data representation"""
    user_id: int
    name: str
    target_amount: Decimal
    target_date: date
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    current_amount: Decimal = Decimal("0.00")
    status: str = "active"
    description: Optional[str] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    auto_transfer_enabled: bool = False
    auto_transfer_amount: Optional[Decimal] = None
    auto_transfer_frequency: Optional[str] = None

@dataclass
class NotificationData:
    """Notification data representation"""
    user_id: int
    type: str
    title: str
    message: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    is_read: bool = False
    action_url: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    priority: str = "normal"

@dataclass
class ContactData:
    """Contact/connection data representation"""
    user_id: int
    contact_id: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "pending"
    nickname: Optional[str] = None
    is_favorite: bool = False
    blocked: bool = False

@dataclass
class MessageData:
    """Message data representation"""
    conversation_id: int
    sender_id: int
    content: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    message_type: str = "text"
    status: str = "sent"
    related_transaction_id: Optional[int] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

@dataclass
class ConversationData:
    """Conversation data representation"""
    created_by_id: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    is_group: bool = False
    name: Optional[str] = None
    last_message_at: Optional[datetime] = None
    participant_ids: List[int] = field(default_factory=list)

@dataclass
class CardData:
    """Payment card data representation"""
    user_id: int
    account_id: int
    card_number: str
    card_type: str
    expiry_date: date
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "active"
    cvv_hash: Optional[str] = None
    pin_hash: Optional[str] = None
    spending_limits: Dict[str, Decimal] = field(default_factory=dict)
    is_contactless_enabled: bool = True
    is_online_enabled: bool = True
    is_international_enabled: bool = True

@dataclass
class SubscriptionData:
    """Subscription data representation"""
    user_id: int
    name: str
    merchant_name: str
    category: str
    amount: Decimal
    billing_cycle: str
    next_billing_date: date
    start_date: date
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "active"
    last_billing_date: Optional[date] = None
    end_date: Optional[date] = None
    free_trial_end_date: Optional[date] = None
    transaction_ids: List[int] = field(default_factory=list)
    detected_automatically: bool = False
    confidence_score: Optional[float] = None

@dataclass
class InvoiceData:
    """Invoice data representation"""
    user_id: int
    invoice_number: str
    client_name: str
    client_email: str
    issue_date: date
    due_date: date
    payment_terms: str
    subtotal: Decimal
    total_amount: Decimal
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "draft"
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None
    client_address: Optional[str] = None

@dataclass
class SecurityEventData:
    """Security event data representation"""
    event_type: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)

# Response/Request specific data classes
@dataclass
class TokenData:
    """JWT token data"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None

@dataclass
class LoginData:
    """Login request data"""
    username: str
    password: str
    remember_me: bool = False

@dataclass
class TransferData:
    """Money transfer data"""
    from_account_id: int
    to_account_id: int
    amount: Decimal
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None

@dataclass
class SearchFilters:
    """Search filter data"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    category_ids: List[int] = field(default_factory=list)
    account_ids: List[int] = field(default_factory=list)
    statuses: List[str] = field(default_factory=list)
    search_text: Optional[str] = None

@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    per_page: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "desc"

@dataclass
class AnalyticsData:
    """Analytics summary data"""
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
    expenses_by_category: Dict[str, Decimal]
    trend_data: List[Dict[str, Any]]
    period: str
    comparison_period: Optional[Dict[str, Any]] = None