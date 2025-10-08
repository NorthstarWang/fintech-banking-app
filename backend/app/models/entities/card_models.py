from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Import shared enums from data_classes
from ..dto import CardStatus, CardType, SpendingLimitPeriod


# Request/Response Models
class VirtualCardCreate(BaseModel):
    account_id: int
    spending_limit: float | None = None
    merchant_restrictions: list[str] | None = None
    expires_in_days: int | None = Field(default=30, ge=1, le=365)
    single_use: bool = False
    name: str | None = None


class VirtualCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    card_number_masked: str
    card_type: CardType
    status: CardStatus
    spending_limit: float | None
    spent_amount: float
    merchant_restrictions: list[str] | None
    single_use: bool
    name: str | None
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    is_virtual: bool | None = None
    parent_card_id: int | None = None


class CardFreezeRequest(BaseModel):
    freeze: bool
    reason: str | None = None


class CardLimitRequest(BaseModel):
    limit_amount: float = Field(gt=0)
    limit_period: SpendingLimitPeriod
    merchant_categories: list[str] | None = None


class CardLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    limit_amount: float
    limit_period: SpendingLimitPeriod
    merchant_categories: list[str] | None
    current_usage: float
    created_at: datetime
    is_active: bool


class CardAnalyticsResponse(BaseModel):
    card_id: int
    total_transactions: int
    total_spent: float
    average_transaction: float
    top_merchants: list[dict]
    spending_by_category: dict
    daily_spending_trend: list[dict]
    fraud_alerts: int
    period_start: datetime
    period_end: datetime
