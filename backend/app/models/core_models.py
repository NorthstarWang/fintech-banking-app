from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Import shared enums from data_classes
from .dto import (
    UserRole, AccountType, TransactionType, TransactionStatus,
    BudgetPeriod, GoalStatus, NotificationType, ContactStatus,
    MessageStatus, PaymentMethodType, PaymentMethodStatus,
    TwoFactorMethod, SecurityEventType, ExportFormat,
    SavingsRuleType, SavingsRuleFrequency, ChallengeStatus,
    ChallengeType, RoundUpStatus, InvoiceStatus, PaymentTerms,
    TaxCategory, ExpenseReportStatus, SubscriptionStatus,
    BillingCycle, SubscriptionCategory, OptimizationSuggestionType
)

# Base Models
class BaseResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# User Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None

class UserResponse(BaseResponse):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    currency: str
    timezone: str
    is_active: bool
    last_login: Optional[datetime] = None

# Account Models
class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: AccountType
    account_number: Optional[str] = None
    institution_name: Optional[str] = None
    initial_balance: float = 0.0
    credit_limit: Optional[float] = None
    interest_rate: Optional[float] = None

class JointAccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: AccountType
    account_number: Optional[str] = None
    institution_name: Optional[str] = None
    initial_balance: float = 0.0
    credit_limit: Optional[float] = None
    interest_rate: Optional[float] = None
    joint_owner_username: str = Field(..., min_length=1)

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    institution_name: Optional[str] = None
    credit_limit: Optional[float] = None
    interest_rate: Optional[float] = None
    is_active: Optional[bool] = None

class AccountResponse(BaseResponse):
    user_id: int
    name: str
    account_type: AccountType
    account_number: Optional[str] = None
    institution_name: Optional[str] = None
    balance: float
    currency: str = "USD"
    credit_limit: Optional[float] = None
    interest_rate: Optional[float] = None
    is_active: bool
    
    @validator('balance', 'credit_limit', pre=True)
    def format_money_fields(cls, v):
        """Ensure all money fields have exactly 2 decimal places."""
        if v is None:
            return v
        return round(float(v), 2)

class AccountSummary(BaseModel):
    total_assets: float
    total_liabilities: float
    net_worth: float
    accounts: List[AccountResponse]
    
    @validator('total_assets', 'total_liabilities', 'net_worth', pre=True)
    def format_money_fields(cls, v):
        """Ensure all money fields have exactly 2 decimal places."""
        if v is None:
            return v
        return round(float(v), 2)

# Category Models
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_income: bool = False

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_income: Optional[bool] = None

class CategoryResponse(BaseResponse):
    user_id: Optional[int] = None  # System categories don't have user_id
    name: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_income: bool
    is_system: bool

# Transaction Models
class TransactionCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    merchant_name: Optional[str] = None
    amount: float = Field(..., gt=0)
    transaction_type: TransactionType
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: datetime
    
    @validator('transaction_type', pre=True)
    def normalize_transaction_type(cls, v):
        if isinstance(v, str):
            # Convert to lowercase for enum matching
            return v.lower()
        return v
    
    @validator('transaction_date', pre=True)
    def parse_transaction_date(cls, v):
        if isinstance(v, str):
            try:
                # Handle date string in ISO format (YYYY-MM-DD)
                if 'T' not in v:
                    v = f"{v}T00:00:00"
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError as e:
                raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD or ISO datetime string")
        return v

class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: datetime

class TransactionResponse(BaseResponse):
    account_id: int
    category_id: Optional[int] = None
    merchant_id: Optional[int] = None
    merchant: Optional[str] = None
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    transaction_date: datetime
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    reference_number: Optional[str] = None
    recurring_rule_id: Optional[int] = None
    
    @validator('amount', pre=True)
    def format_money_fields(cls, v):
        """Ensure all money fields have exactly 2 decimal places."""
        if v is None:
            return v
        return round(float(v), 2)

class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    transaction_type: Optional[TransactionType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

# Budget Models
class BudgetCreate(BaseModel):
    category_id: int
    amount: float = Field(..., gt=0)
    period: BudgetPeriod
    start_date: date
    end_date: Optional[date] = None
    alert_threshold: float = Field(0.8, ge=0, le=1)

class BudgetUpdate(BaseModel):
    amount: Optional[float] = None
    alert_threshold: Optional[float] = None
    is_active: Optional[bool] = None

class BudgetResponse(BaseResponse):
    user_id: int
    category_id: int
    amount: float
    period: BudgetPeriod
    start_date: date
    end_date: Optional[date] = None
    alert_threshold: float
    is_active: bool
    spent_amount: Optional[float] = None  # Calculated field
    remaining_amount: Optional[float] = None  # Calculated field
    percentage_used: Optional[float] = None  # Calculated field
    
    @validator('amount', 'spent_amount', 'remaining_amount', pre=True)
    def format_money_fields(cls, v):
        """Ensure all money fields have exactly 2 decimal places."""
        if v is None:
            return v
        return round(float(v), 2)

# Goal Models
class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    target_amount: float = Field(..., gt=0)
    target_date: Optional[date] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    initial_amount: Optional[float] = None
    account_id: Optional[int] = None
    auto_transfer_amount: Optional[float] = None
    auto_transfer_frequency: Optional[str] = None
    # Automatic allocation fields
    auto_allocate_percentage: Optional[float] = Field(None, ge=0, le=100)
    auto_allocate_fixed_amount: Optional[float] = Field(None, ge=0)
    allocation_priority: Optional[int] = Field(1, ge=1)
    allocation_source_types: Optional[List[str]] = None

class GoalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[date] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[GoalStatus] = None
    auto_transfer_amount: Optional[float] = None
    auto_transfer_frequency: Optional[str] = None
    # Automatic allocation fields
    auto_allocate_percentage: Optional[float] = Field(None, ge=0, le=100)
    auto_allocate_fixed_amount: Optional[float] = Field(None, ge=0)
    allocation_priority: Optional[int] = Field(None, ge=1)
    allocation_source_types: Optional[List[str]] = None

class GoalContribute(BaseModel):
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None

class GoalResponse(BaseResponse):
    user_id: int
    name: str
    description: Optional[str] = None
    target_amount: float
    current_amount: float
    target_date: Optional[date] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: GoalStatus
    account_id: Optional[int] = None
    auto_transfer_amount: Optional[float] = None
    auto_transfer_frequency: Optional[str] = None
    completed_at: Optional[datetime] = None
    progress_percentage: Optional[float] = None  # Calculated field
    # Automatic allocation fields
    auto_allocate_percentage: Optional[float] = None
    auto_allocate_fixed_amount: Optional[float] = None
    allocation_priority: Optional[int] = None
    allocation_source_types: Optional[List[str]] = None
    
    @validator('target_amount', 'current_amount', 'auto_transfer_amount', 'auto_allocate_fixed_amount', pre=True)
    def format_money_fields(cls, v):
        """Ensure all money fields have exactly 2 decimal places."""
        if v is None:
            return v
        return round(float(v), 2)

# Notification Models
class NotificationResponse(BaseResponse):
    user_id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    read_at: Optional[datetime] = None

class NotificationUpdate(BaseModel):
    is_read: bool

# Recurring Transaction Models
class RecurringRuleCreate(BaseModel):
    name: str
    account_id: int
    category_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    transaction_type: TransactionType
    frequency: str  # daily, weekly, monthly, yearly
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_date: date
    end_date: Optional[date] = None

class RecurringRuleResponse(BaseResponse):
    user_id: int
    name: str
    account_id: int
    category_id: Optional[int] = None
    amount: float
    transaction_type: TransactionType
    frequency: str
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    start_date: date
    end_date: Optional[date] = None
    next_occurrence: Optional[date] = None
    is_active: bool

# Import Models
class ImportFileRequest(BaseModel):
    account_id: int
    file_content: str  # Base64 encoded CSV content

class ImportFileResponse(BaseResponse):
    user_id: int
    filename: str
    account_id: Optional[int] = None
    transactions_count: int
    status: str
    error_message: Optional[str] = None

# Analytics Models
class SpendingByCategory(BaseModel):
    category_id: int
    category_name: str
    total_amount: float
    transaction_count: int
    percentage: float

class IncomeExpenseSummary(BaseModel):
    period: str
    total_income: float
    total_expenses: float
    net_income: float
    income_by_category: List[SpendingByCategory]
    expenses_by_category: List[SpendingByCategory]

class BudgetSummary(BaseModel):
    total_budget: float  # Changed from total_budgeted to match frontend
    total_spent: float
    total_remaining: float
    budgets: List[BudgetResponse]

class GoalSummary(BaseModel):
    total_goals: int
    active_goals: int
    completed_goals: int
    total_target: float
    total_saved: float
    goals: List[GoalResponse]
    
    @validator('total_target', 'total_saved', pre=True)
    def format_money_fields(cls, v):
        """Ensure all money fields have exactly 2 decimal places."""
        if v is None:
            return v
        return round(float(v), 2)

# Contact Models
class ContactCreate(BaseModel):
    contact_id: int
    nickname: Optional[str] = None

class ContactUpdate(BaseModel):
    nickname: Optional[str] = None
    is_favorite: Optional[bool] = None

class ContactStatusUpdate(BaseModel):
    status: ContactStatus

class ContactResponse(BaseResponse):
    user_id: int
    contact_id: int
    status: ContactStatus
    nickname: Optional[str] = None
    is_favorite: bool
    contact_username: Optional[str] = None  # Populated from joins
    contact_email: Optional[str] = None  # Populated from joins

# Conversation Models
class ConversationCreate(BaseModel):
    participant_ids: List[int]  # User IDs to add to conversation
    title: Optional[str] = None  # For group chats
    initial_message: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseResponse):
    title: Optional[str] = None
    is_group: bool
    created_by_id: Optional[int] = None
    last_message_at: Optional[datetime] = None
    participant_count: Optional[int] = None
    unread_count: Optional[int] = None  # Calculated per user

class ConversationParticipantResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    joined_at: datetime
    last_read_at: Optional[datetime] = None
    is_admin: bool
    is_muted: bool
    notification_enabled: bool
    username: Optional[str] = None  # From join
    
    class Config:
        from_attributes = True

# Message Models
class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    message_type: str = "text"
    related_transaction_id: Optional[int] = None

class MessageUpdate(BaseModel):
    content: str

class MessageResponse(BaseResponse):
    conversation_id: int
    sender_id: int
    content: str
    message_type: str
    related_transaction_id: Optional[int] = None
    status: MessageStatus
    is_edited: bool
    edited_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    sender_username: Optional[str] = None  # From join
    read_by_count: Optional[int] = None  # Calculated

class MessageReadReceiptResponse(BaseModel):
    message_id: int
    user_id: int
    read_at: datetime
    username: Optional[str] = None  # From join
    
    class Config:
        from_attributes = True

# Chat Analytics
class ChatSummary(BaseModel):
    total_conversations: int
    active_conversations: int  # With messages in last 30 days
    total_messages: int
    total_contacts: int
    pending_contact_requests: int

# Direct Message Models
class DirectMessageCreate(BaseModel):
    recipient_username: str
    subject: str
    message: str
    priority: str = "normal"
    attachments: Optional[List[Dict[str, Any]]] = None
    is_draft: bool = False

class DirectMessageReply(BaseModel):
    message: str

class DirectMessageResponse(BaseResponse):
    sender_id: int
    sender_username: Optional[str] = None
    recipient_id: int
    recipient_username: Optional[str] = None
    subject: str
    message: str
    priority: str
    is_read: bool
    read_at: Optional[datetime] = None
    is_draft: bool
    parent_message_id: Optional[int] = None
    folder_id: Optional[int] = None
    sent_at: datetime
    attachments: Optional[List[Dict[str, Any]]] = []
    
    @property
    def preview(self) -> str:
        return self.message[:100] + "..." if len(self.message) > 100 else self.message
    
    @classmethod
    def from_orm(cls, obj):
        # Create instance without attachments
        data = {
            "id": obj.id,
            "sender_id": obj.sender_id,
            "recipient_id": obj.recipient_id,
            "subject": obj.subject,
            "message": obj.message,
            "priority": obj.priority,
            "is_read": obj.is_read,
            "read_at": obj.read_at,
            "is_draft": obj.is_draft,
            "parent_message_id": obj.parent_message_id,
            "folder_id": obj.folder_id,
            "sent_at": obj.sent_at,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "attachments": []  # Will be populated separately
        }
        return cls(**data)

class MessageFolderCreate(BaseModel):
    folder_name: str
    color: Optional[str] = None

class MessageFolderResponse(BaseResponse):
    user_id: int
    folder_name: str
    color: Optional[str] = None
    message_count: Optional[int] = 0

class MessageMoveRequest(BaseModel):
    folder_id: int

class MessageSettingsUpdate(BaseModel):
    email_on_new_message: Optional[bool] = None
    push_notifications: Optional[bool] = None
    notification_sound: Optional[bool] = None
    auto_mark_read: Optional[bool] = None

class MessageSettingsResponse(BaseModel):
    user_id: int
    email_on_new_message: bool
    push_notifications: bool
    notification_sound: bool
    auto_mark_read: bool
    
    class Config:
        from_attributes = True

class BlockUserRequest(BaseModel):
    username: str
    reason: Optional[str] = None

class BulkMessageUpdate(BaseModel):
    message_ids: List[int]

# Payment Method Models
class PaymentMethodBase(BaseModel):
    type: PaymentMethodType
    nickname: Optional[str] = None
    is_default: bool = False

class PaymentMethodCardCreate(PaymentMethodBase):
    type: PaymentMethodType = PaymentMethodType.CREDIT_CARD
    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=datetime.now().year)
    cvv: str = Field(..., min_length=3, max_length=4)
    billing_zip: str

class PaymentMethodBankCreate(PaymentMethodBase):
    type: PaymentMethodType = PaymentMethodType.BANK_ACCOUNT
    account_number: str
    routing_number: str = Field(..., pattern="^[0-9]{9}$")
    bank_name: str
    account_type: str = Field(..., pattern="^(checking|savings)$")

class PaymentMethodWalletCreate(PaymentMethodBase):
    type: PaymentMethodType = PaymentMethodType.DIGITAL_WALLET
    wallet_provider: str
    wallet_id: str

class PaymentMethodUpdate(BaseModel):
    nickname: Optional[str] = None
    is_default: Optional[bool] = None
    billing_zip: Optional[str] = None

class PaymentMethodResponse(PaymentMethodBase):
    id: int
    status: PaymentMethodStatus
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    account_last_four: Optional[str] = None
    bank_name: Optional[str] = None
    wallet_provider: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Two-Factor Authentication Models
class TwoFactorSetup(BaseModel):
    method: TwoFactorMethod
    phone_number: Optional[str] = None  # For SMS
    email: Optional[str] = None  # For email verification

class TwoFactorVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    method: TwoFactorMethod

class TwoFactorResponse(BaseModel):
    id: int
    method: TwoFactorMethod
    is_enabled: bool
    is_primary: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TwoFactorSetupResponse(TwoFactorResponse):
    secret: Optional[str] = None  # For TOTP setup
    qr_code: Optional[str] = None  # QR code image data
    backup_codes: Optional[List[str]] = None  # One-time backup codes

# Device/Session Models
class UserDeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: str
    device_type: str
    os: Optional[str] = None
    browser: Optional[str] = None
    location: Optional[str] = None
    is_trusted: bool
    is_active: bool
    created_at: datetime
    last_active_at: datetime
    
    class Config:
        from_attributes = True

class DeviceTrustUpdate(BaseModel):
    is_trusted: bool

# Security Audit Log Models
class SecurityAuditLogResponse(BaseModel):
    id: int
    event_type: SecurityEventType
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transaction Attachment Models
class TransactionAttachment(BaseModel):
    id: int
    transaction_id: int
    file_name: str
    file_type: str
    file_size: int
    file_url: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class TransactionAttachmentCreate(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    file_data: str  # Base64 encoded file data

# Transaction Split Models
class TransactionSplitCreate(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)
    description: Optional[str] = None

class TransactionSplitResponse(BaseModel):
    id: int
    transaction_id: int
    user_id: int
    amount: float
    is_paid: bool
    paid_at: Optional[datetime] = None
    description: Optional[str] = None
    user_name: Optional[str] = None  # From join
    
    class Config:
        from_attributes = True

# Export Models
class ExportRequest(BaseModel):
    format: ExportFormat
    start_date: date
    end_date: date
    account_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None
    include_attachments: bool = False

class ExportResponse(BaseModel):
    export_id: str
    status: str  # pending, processing, completed, failed
    format: ExportFormat
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# Currency Models
class CurrencyInfo(BaseModel):
    code: str
    name: str
    symbol: str
    exchange_rate: float  # Rate to USD

class CurrencyConversion(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    exchange_rate: float
    conversion_date: datetime

# Bank Linking Models
class BankLinkRequest(BaseModel):
    institution_id: str
    credentials: Dict[str, str]  # Bank-specific credentials

class BankLinkResponse(BaseModel):
    link_id: str
    institution_name: str
    status: str  # pending, active, error, expired
    accounts_found: int
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None

class LinkedAccountResponse(BaseModel):
    id: int
    external_id: str
    institution_name: str
    account_name: str
    account_type: AccountType
    account_number_masked: str
    current_balance: float
    available_balance: float
    last_sync: datetime

# Transfer and Payment Models
class TransferRequest(BaseModel):
    source_account_id: int
    destination_account_id: int
    amount: float = Field(..., gt=0, le=50000)  # Max 50k per transfer
    description: Optional[str] = None
    is_external: bool = False

class DepositRequest(BaseModel):
    account_id: int
    amount: float = Field(..., gt=0, le=100000)  # Max 100k per deposit
    description: Optional[str] = None
    deposit_method: str = Field(..., pattern="^(cash|check|wire|ach|mobile)$")
    source: Optional[str] = None

class WithdrawalRequest(BaseModel):
    account_id: int
    amount: float = Field(..., gt=0, le=10000)  # Max 10k per withdrawal
    description: Optional[str] = None
    withdrawal_method: str = Field(..., pattern="^(atm|bank|wire|check)$")

class BillPaymentRequest(BaseModel):
    account_id: int
    amount: float = Field(..., gt=0)
    payee_name: str
    payee_account_number: str
    bill_type: str = Field(..., pattern="^(utility|credit_card|loan|rent|insurance|other_bills|other)$")
    category_id: Optional[int] = None
    due_date: Optional[date] = None
    description: Optional[str] = None

class TransferResponse(TransactionResponse):
    """Transfer response is the same as TransactionResponse"""
    pass

# Import new feature models
# Note: These are imported separately in each route file that needs them
# The duplicate models below have been removed to avoid conflicts
# Models are now properly organized in:
# - app.models.card_models
# - app.models.credit_models
# - app.models.savings_models
# - app.models.business_models
# - app.models.subscription_models