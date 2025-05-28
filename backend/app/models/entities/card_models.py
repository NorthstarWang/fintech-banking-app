from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Import shared enums from data_classes
from ..dto import CardStatus, CardType, SpendingLimitPeriod


# Request/Response Models
class VirtualCardCreate(BaseModel):
    account_id: int
    spending_limit: Optional[float] = None
    merchant_restrictions: Optional[List[str]] = None
    expires_in_days: Optional[int] = Field(default=30, ge=1, le=365)
    single_use: bool = False
    name: Optional[str] = None


class VirtualCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    card_number_masked: str
    card_type: CardType
    status: CardStatus
    spending_limit: Optional[float]
    spent_amount: float
    merchant_restrictions: Optional[List[str]]
    single_use: bool
    name: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_virtual: Optional[bool] = None
    parent_card_id: Optional[int] = None


class CardFreezeRequest(BaseModel):
    freeze: bool
    reason: Optional[str] = None


class CardLimitRequest(BaseModel):
    limit_amount: float = Field(gt=0)
    limit_period: SpendingLimitPeriod
    merchant_categories: Optional[List[str]] = None


class CardLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    card_id: int
    limit_amount: float
    limit_period: SpendingLimitPeriod
    merchant_categories: Optional[List[str]]
    current_usage: float
    created_at: datetime
    is_active: bool


class CardAnalyticsResponse(BaseModel):
    card_id: int
    total_transactions: int
    total_spent: float
    average_transaction: float
    top_merchants: List[dict]
    spending_by_category: dict
    daily_spending_trend: List[dict]
    fraud_alerts: int
    period_start: datetime
    period_end: datetime