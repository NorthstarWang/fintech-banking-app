"""
Base data classes and shared models used across the application.
These provide type safety and consistency between different layers.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class UserData:
    """User data representation"""
    username: str
    email: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    password_hash: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str = "user"
    currency: str = "USD"
    timezone: str = "UTC"
    is_active: bool = True
    last_login: datetime | None = None
    two_factor_enabled: bool = False
    two_factor_secret: str | None = None

@dataclass
class AccountData:
    """Account data representation"""
    user_id: int
    name: str
    account_type: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    account_number: str | None = None
    routing_number: str | None = None
    institution_name: str | None = None
    balance: Decimal = Decimal("0.00")
    currency: str = "USD"
    is_active: bool = True
    credit_limit: Decimal | None = None
    interest_rate: float | None = None

@dataclass
class TransactionData:
    """Transaction data representation"""
    account_id: int
    amount: Decimal
    transaction_type: str
    transaction_date: datetime
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "completed"
    description: str | None = None
    category_id: int | None = None
    merchant_id: int | None = None
    reference_number: str | None = None
    from_account_id: int | None = None
    to_account_id: int | None = None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    location: str | None = None
    receipt_url: str | None = None

@dataclass
class CategoryData:
    """Category data representation"""
    name: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    icon: str | None = "📁"
    color: str | None = "#6B7280"
    is_income: bool = False
    is_system: bool = False
    user_id: int | None = None
    parent_id: int | None = None
    budget_amount: Decimal | None = None

@dataclass
class BudgetData:
    """Budget data representation"""
    user_id: int
    category_id: int
    amount: Decimal
    period: str
    start_date: date
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    end_date: date | None = None
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
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    current_amount: Decimal = Decimal("0.00")
    status: str = "active"
    description: str | None = None
    account_id: int | None = None
    category_id: int | None = None
    auto_transfer_enabled: bool = False
    auto_transfer_amount: Decimal | None = None
    auto_transfer_frequency: str | None = None

@dataclass
class NotificationData:
    """Notification data representation"""
    user_id: int
    type: str
    title: str
    message: str
    id: int | None = None
    created_at: datetime | None = None
    is_read: bool = False
    action_url: str | None = None
    related_entity_type: str | None = None
    related_entity_id: int | None = None
    priority: str = "normal"

@dataclass
class ContactData:
    """Contact/connection data representation"""
    user_id: int
    contact_id: int
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "pending"
    nickname: str | None = None
    is_favorite: bool = False
    blocked: bool = False

@dataclass
class MessageData:
    """Message data representation"""
    conversation_id: int
    sender_id: int
    content: str
    id: int | None = None
    created_at: datetime | None = None
    message_type: str = "text"
    status: str = "sent"
    related_transaction_id: int | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    edited_at: datetime | None = None
    deleted_at: datetime | None = None

@dataclass
class ConversationData:
    """Conversation data representation"""
    created_by_id: int
    id: int | None = None
    created_at: datetime | None = None
    is_group: bool = False
    name: str | None = None
    last_message_at: datetime | None = None
    participant_ids: list[int] = field(default_factory=list)

@dataclass
class CardData:
    """Payment card data representation"""
    user_id: int
    account_id: int
    card_number: str
    card_type: str
    expiry_date: date
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "active"
    cvv_hash: str | None = None
    pin_hash: str | None = None
    spending_limits: dict[str, Decimal] = field(default_factory=dict)
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
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "active"
    last_billing_date: date | None = None
    end_date: date | None = None
    free_trial_end_date: date | None = None
    transaction_ids: list[int] = field(default_factory=list)
    detected_automatically: bool = False
    confidence_score: float | None = None

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
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "draft"
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    line_items: list[dict[str, Any]] = field(default_factory=list)
    notes: str | None = None
    client_address: str | None = None

@dataclass
class SecurityEventData:
    """Security event data representation"""
    event_type: str
    id: int | None = None
    created_at: datetime | None = None
    user_id: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    success: bool = True
    details: dict[str, Any] = field(default_factory=dict)

# Response/Request specific data classes
@dataclass
class TokenData:
    """JWT token data"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: str | None = None

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
    description: str | None = None
    scheduled_date: datetime | None = None

@dataclass
class SearchFilters:
    """Search filter data"""
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    category_ids: list[int] = field(default_factory=list)
    account_ids: list[int] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
    search_text: str | None = None

@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    per_page: int = 20
    sort_by: str | None = None
    sort_order: str = "desc"

@dataclass
class AnalyticsData:
    """Analytics summary data"""
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
    expenses_by_category: dict[str, Decimal]
    trend_data: list[dict[str, Any]]
    period: str
    comparison_period: dict[str, Any] | None = None
