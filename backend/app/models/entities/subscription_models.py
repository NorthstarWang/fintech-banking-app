from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

# Import shared enums from data_classes
from ..dto import (
    SubscriptionStatus, BillingCycle, SubscriptionCategory,
    OptimizationSuggestionType
)


# Request/Response Models
class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    merchant_name: str
    category: SubscriptionCategory
    status: SubscriptionStatus
    amount: float
    billing_cycle: BillingCycle
    next_billing_date: date
    last_billing_date: Optional[date]
    start_date: date
    end_date: Optional[date]
    free_trial_end_date: Optional[date]
    transaction_ids: List[int]
    detected_automatically: bool
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    # Additional fields for trial tracking
    is_trial: Optional[bool] = False
    regular_price: Optional[float] = None
    days_until_billing: Optional[int] = None


class SubscriptionUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[SubscriptionCategory] = None
    status: Optional[SubscriptionStatus] = None
    amount: Optional[float] = None
    billing_cycle: Optional[BillingCycle] = None
    next_billing_date: Optional[date] = None
    notes: Optional[str] = None


class SubscriptionAnalysisResponse(BaseModel):
    total_subscriptions: int
    active_subscriptions: int
    total_monthly_cost: float
    total_annual_cost: float
    cost_by_category: Dict[str, float]
    cost_trend: List[Dict[str, Any]]  # Monthly costs over time
    most_expensive: List[Dict[str, Any]]
    least_used: List[Dict[str, Any]]
    upcoming_renewals: List[Dict[str, Any]]
    savings_opportunities: float
    average_subscription_cost: float


class CancellationReminderRequest(BaseModel):
    days_before: int = Field(ge=1, le=90)
    reason: Optional[str] = None
    target_date: Optional[date] = None


class CancellationReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    subscription_id: int
    user_id: int
    reminder_date: date
    reason: Optional[str]
    is_sent: bool
    created_at: datetime


class OptimizationSuggestion(BaseModel):
    subscription_id: int
    subscription_name: str
    suggestion_type: OptimizationSuggestionType
    current_cost: float
    potential_savings: float
    alternative_name: Optional[str]
    alternative_cost: Optional[float]
    reason: str
    confidence: float  # 0-1 score
    action_steps: List[str]


class OptimizationResponse(BaseModel):
    total_potential_savings: float
    suggestions: List[OptimizationSuggestion]
    bundling_opportunities: List[Dict[str, Any]]
    unused_subscriptions: List[Dict[str, Any]]
    duplicate_services: List[Dict[str, Any]]
    optimization_score: float  # 0-100
    generated_at: datetime


# Additional request/response models for missing endpoints
class SubscriptionCreateRequest(BaseModel):
    service_name: str
    category: SubscriptionCategory
    amount: float
    billing_cycle: BillingCycle
    start_date: Optional[date] = None
    payment_method_id: Optional[int] = None
    auto_renew: Optional[bool] = True
    description: Optional[str] = None
    is_trial: Optional[bool] = False
    trial_end_date: Optional[date] = None
    regular_price: Optional[float] = None
    shareable: Optional[bool] = False
    max_users: Optional[int] = 1


class SubscriptionDetailResponse(SubscriptionResponse):
    payment_history: List[Dict[str, Any]]
    total_spent: float
    days_until_billing: Optional[int] = None


class SubscriptionCancelRequest(BaseModel):
    cancel_at_period_end: bool = True


class SubscriptionCancelResponse(BaseModel):
    id: int
    status: SubscriptionStatus
    cancellation_date: date
    message: str


class SubscriptionPauseRequest(BaseModel):
    pause_until: date


class SubscriptionPauseResponse(BaseModel):
    id: int
    status: SubscriptionStatus
    resume_date: date
    message: str


class SubscriptionSummaryResponse(BaseModel):
    total_monthly_cost: float
    total_annual_cost: float
    active_subscriptions: int
    paused_subscriptions: int
    cancelled_subscriptions: int
    by_category: Dict[str, float]


class PaymentHistoryResponse(BaseModel):
    amount: float
    payment_date: date
    status: str
    payment_method: str
    transaction_id: Optional[int] = None


class SubscriptionReminderRequest(BaseModel):
    payment_reminder: bool
    reminder_days_before: int = Field(ge=1, le=30)
    cancellation_reminder: bool
    price_increase_alert: bool


class SubscriptionReminderResponse(BaseModel):
    subscription_id: int
    payment_reminder: bool
    reminder_days_before: int
    cancellation_reminder: bool
    price_increase_alert: bool
    message: str


class SubscriptionUsageRequest(BaseModel):
    usage_date: datetime
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class SubscriptionUsageResponse(BaseModel):
    message: str


class SubscriptionRecommendationsResponse(BaseModel):
    unused_subscriptions: List[Dict[str, Any]]
    duplicate_services: List[Dict[str, Any]]
    savings_opportunities: List[Dict[str, Any]]
    total_potential_savings: float


class SubscriptionShareRequest(BaseModel):
    share_with_username: str
    cost_split_percentage: float = Field(ge=0, le=100)


class SubscriptionShareResponse(BaseModel):
    id: int
    shared_users: List[Dict[str, Any]]
    message: str


class BulkImportRequest(BaseModel):
    subscriptions: List[Dict[str, Any]]


class BulkImportResponse(BaseModel):
    imported: int
    subscription_ids: List[int]
    errors: List[str] = []