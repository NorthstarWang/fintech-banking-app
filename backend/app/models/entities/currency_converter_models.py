"""
Virtual currency converter models (Airtm-like system).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Currency converter specific enums
class CurrencyType(str, Enum):
    FIAT = "fiat"
    CRYPTO = "crypto"
    VIRTUAL = "virtual"

class TransferMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    WIRE_TRANSFER = "wire_transfer"
    CRYPTO_WALLET = "crypto_wallet"
    PAYPAL = "paypal"
    SKRILL = "skrill"
    PAYONEER = "payoneer"
    WISE = "wise"
    ZELLE = "zelle"
    CASH_PICKUP = "cash_pickup"

class TransferStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"

class PeerStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    SUSPENDED = "suspended"

class VerificationLevel(str, Enum):
    UNVERIFIED = "unverified"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PREMIUM = "premium"

class FeeType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    TIERED = "tiered"

# Request/Response Models
class CurrencyPair(BaseModel):
    from_currency: str
    to_currency: str
    from_type: CurrencyType
    to_type: CurrencyType

class ExchangeRateResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float}
    )
    
    currency_pair: CurrencyPair
    rate: Decimal
    spread: Decimal
    effective_rate: Decimal
    fee_percentage: Decimal
    minimum_amount: Decimal
    maximum_amount: Decimal
    estimated_arrival: str  # e.g., "instant", "1-3 days"
    last_updated: datetime
    is_available: bool

class ConversionQuoteRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    transfer_method: Optional[TransferMethod] = None

class ConversionQuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    quote_id: str
    from_currency: str
    to_currency: str
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal
    fee_amount: Decimal
    fee_percentage: Decimal
    total_cost: Decimal
    you_receive: Decimal
    transfer_method: Optional[TransferMethod]
    estimated_completion: str
    expires_at: datetime
    breakdown: Dict[str, Any]

class ConversionOrderCreate(BaseModel):
    quote_id: str
    recipient_details: Dict[str, Any]  # Bank account, wallet address, etc.
    purpose: Optional[str] = None
    reference: Optional[str] = None

class ConversionOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_number: str
    user_id: int
    status: TransferStatus
    from_currency: str
    to_currency: str
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal
    fee_amount: Decimal
    transfer_method: TransferMethod
    recipient_details: Dict[str, Any]
    purpose: Optional[str]
    reference: Optional[str]
    peer_id: Optional[int]  # If P2P transfer
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    tracking_updates: List[Dict[str, Any]]

class PeerOfferCreate(BaseModel):
    currency: str
    currency_type: CurrencyType
    amount_available: float
    rate_adjustment: float  # Percentage above/below market rate
    transfer_methods: List[TransferMethod]
    min_transaction: float
    max_transaction: float
    availability_hours: Dict[str, str]  # {"monday": "9:00-17:00", ...}

class PeerOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    peer_id: int
    peer_username: str
    peer_rating: float
    peer_completed_trades: int
    peer_verification_level: VerificationLevel
    currency: str
    currency_type: CurrencyType
    amount_available: Decimal
    amount_remaining: Decimal
    rate: Decimal
    transfer_methods: List[TransferMethod]
    min_transaction: Decimal
    max_transaction: Decimal
    response_time_minutes: int
    is_online: bool
    last_seen: datetime
    created_at: datetime

class P2PTradeRequest(BaseModel):
    offer_id: int
    amount: float
    transfer_method: TransferMethod
    payment_details: Dict[str, Any]

class P2PTradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    trade_number: str
    buyer_id: int
    seller_id: int
    offer_id: int
    status: TransferStatus
    amount: Decimal
    currency: str
    rate: Decimal
    total_cost: Decimal
    fee_amount: Decimal
    transfer_method: TransferMethod
    payment_details: Dict[str, Any]
    chat_enabled: bool
    escrow_released: bool
    dispute_id: Optional[int]
    created_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime]

class CurrencyBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    currency: str
    currency_type: CurrencyType
    balance: Decimal
    available_balance: Decimal
    pending_balance: Decimal
    total_converted: Decimal
    last_activity: Optional[datetime]

class ConversionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    total_conversions: int
    total_volume: Decimal
    currencies_used: List[str]
    favorite_pairs: List[CurrencyPair]
    average_fee_percentage: Decimal
    total_fees_paid: Decimal
    member_since: date
    verification_level: VerificationLevel

class CurrencySupportedResponse(BaseModel):
    code: str
    name: str
    type: CurrencyType
    symbol: str
    decimal_places: int
    min_amount: Decimal
    max_amount: Decimal
    is_active: bool
    supported_methods: List[TransferMethod]
    countries: List[str]
    
class TransferLimitResponse(BaseModel):
    verification_level: VerificationLevel
    daily_limit: Decimal
    monthly_limit: Decimal
    per_transaction_limit: Decimal
    daily_remaining: Decimal
    monthly_remaining: Decimal
    next_limit_reset: datetime
    upgrade_available: bool
    
class ComplianceCheckResponse(BaseModel):
    transaction_allowed: bool
    requires_additional_info: bool
    required_documents: List[str]
    aml_score: float
    risk_level: str
    notes: Optional[str]