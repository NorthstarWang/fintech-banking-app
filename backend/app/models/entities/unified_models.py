from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Unified system enums
class AssetClass(str, Enum):
    FIAT = "fiat"
    CRYPTO = "crypto"
    NFT = "nft"
    CREDIT = "credit"
    LOAN = "loan"
    INSURANCE = "insurance"
    INVESTMENT = "investment"

class ConversionType(str, Enum):
    FIAT_TO_CRYPTO = "fiat_to_crypto"
    CRYPTO_TO_FIAT = "crypto_to_fiat"
    CRYPTO_TO_CRYPTO = "crypto_to_crypto"
    CREDIT_TO_FIAT = "credit_to_fiat"
    COLLATERAL_SWAP = "collateral_swap"

class TransferStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Request/Response Models
class UnifiedBalanceResponse(BaseModel):
    """Aggregated balance across all asset types"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    total_net_worth_usd: float
    
    # Traditional assets
    fiat_assets: Dict[str, float]  # currency -> amount
    total_fiat_usd: float
    
    # Digital assets
    crypto_assets: Dict[str, Dict[str, Any]]  # symbol -> {amount, usd_value}
    nft_collection_value: float
    total_crypto_usd: float
    
    # Credit available
    total_credit_available: float
    credit_utilization: float
    
    # Liabilities
    total_loans: float
    total_monthly_obligations: float
    
    # Insurance
    total_coverage_amount: float
    insurance_types_covered: List[str]
    
    # DeFi positions
    defi_positions_value: float
    defi_yield_annual: float
    
    # Calculated metrics
    debt_to_asset_ratio: float
    liquid_assets: float
    illiquid_assets: float
    
    last_updated: datetime

class AssetBridgeRequest(BaseModel):
    """Request to bridge/convert between different asset types"""
    from_asset_class: AssetClass
    from_asset_id: str  # Could be account_id, wallet_id, etc.
    from_amount: Union[float, str]  # String for crypto precision
    to_asset_class: AssetClass
    to_asset_id: Optional[str] = None
    to_asset_type: Optional[str] = None  # e.g., "USDC", "USD"
    notes: Optional[str] = None

class AssetBridgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    bridge_type: ConversionType
    from_asset_class: AssetClass
    from_asset_id: str
    from_amount: str
    from_asset_name: str
    to_asset_class: AssetClass
    to_asset_id: str
    to_amount: str
    to_asset_name: str
    exchange_rate: float
    fees: Dict[str, float]  # fee_type -> amount
    total_fees_usd: float
    status: TransferStatus
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None

class UnifiedTransferRequest(BaseModel):
    """Smart transfer that finds optimal route"""
    recipient_identifier: str  # username, email, wallet address, etc.
    amount_usd: float
    preferred_method: Optional[str] = None  # Let system choose if None
    preferred_currency: Optional[str] = "USD"
    notes: Optional[str] = None
    
class UnifiedTransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sender_id: int
    recipient_id: Optional[int] = None
    recipient_identifier: str
    amount_requested_usd: float
    
    # Route details
    route_taken: List[Dict[str, Any]]  # Steps in the transfer
    source_assets: List[Dict[str, Any]]  # Assets used
    
    # Final amounts
    amount_sent: str
    amount_sent_currency: str
    amount_received: str
    amount_received_currency: str
    
    # Fees and timing
    total_fees_usd: float
    exchange_rate: Optional[float] = None
    estimated_arrival: datetime
    
    status: TransferStatus
    initiated_at: datetime
    completed_at: Optional[datetime] = None

class CollateralPositionResponse(BaseModel):
    """Cross-asset collateral positions"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    position_type: str  # loan, credit_line, etc.
    
    # Collateral details
    collateral_assets: List[Dict[str, Any]]  # Multiple assets as collateral
    total_collateral_value_usd: float
    
    # Borrowed/utilized
    amount_borrowed: float
    currency_borrowed: str
    
    # Risk metrics
    loan_to_value: float  # Current LTV
    liquidation_ltv: float  # LTV at which liquidation occurs
    health_factor: float  # How close to liquidation
    
    # Terms
    interest_rate: float
    interest_type: str  # fixed, variable
    
    created_at: datetime
    last_updated: datetime

class CrossAssetOpportunity(BaseModel):
    """Opportunities identified across different asset classes"""
    opportunity_type: str  # arbitrage, yield, refinance, etc.
    description: str
    potential_gain_usd: float
    risk_level: str  # low, medium, high
    
    # Required actions
    actions_required: List[Dict[str, Any]]
    
    # Assets involved
    assets_involved: List[Dict[str, Any]]
    
    # Time sensitivity
    expires_at: Optional[datetime] = None
    optimal_execution_time: Optional[datetime] = None
    
    # Requirements
    minimum_capital: Optional[float] = None
    prerequisites: List[str]

class PortfolioOptimizationRequest(BaseModel):
    optimization_goal: str  # maximize_yield, minimize_risk, balance
    risk_tolerance: str  # conservative, moderate, aggressive
    time_horizon_days: int
    constraints: Optional[Dict[str, Any]] = None  # e.g., keep_minimum_checking

class PortfolioOptimizationResponse(BaseModel):
    current_allocation: Dict[str, float]  # asset_class -> percentage
    recommended_allocation: Dict[str, float]
    
    # Specific moves
    recommended_actions: List[Dict[str, Any]]
    
    # Expected outcomes
    expected_return_annual: float
    risk_score: float  # 1-10
    
    # Benefits
    estimated_additional_yield: float
    risk_reduction: float
    
    # Execution plan
    execution_steps: List[Dict[str, Any]]
    estimated_fees: float
    
class UnifiedSearchRequest(BaseModel):
    query: str
    asset_classes: Optional[List[AssetClass]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    
class UnifiedSearchResponse(BaseModel):
    results: List[Dict[str, Any]]  # Transactions across all systems
    total_results: int
    grouping: Dict[str, List[Dict[str, Any]]]  # By asset class
    aggregations: Dict[str, float]  # Sum by type, etc.