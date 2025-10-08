from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Import shared enums from data_classes
from ..dto import BillingCycle, OptimizationSuggestionType, SubscriptionCategory, SubscriptionStatus


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
    last_billing_date: date | None
    start_date: date
    end_date: date | None
    free_trial_end_date: date | None
    transaction_ids: list[int]
    detected_automatically: bool
    confidence_score: float | None
    created_at: datetime
    updated_at: datetime
    # Additional fields for trial tracking
    is_trial: bool | None = False
    regular_price: float | None = None
    days_until_billing: int | None = None


class SubscriptionUpdateRequest(BaseModel):
    name: str | None = None
    category: SubscriptionCategory | None = None
    status: SubscriptionStatus | None = None
    amount: float | None = None
    billing_cycle: BillingCycle | None = None
    next_billing_date: date | None = None
    notes: str | None = None


class SubscriptionAnalysisResponse(BaseModel):
    total_subscriptions: int
    active_subscriptions: int
    total_monthly_cost: float
    total_annual_cost: float
    cost_by_category: dict[str, float]
    cost_trend: list[dict[str, Any]]  # Monthly costs over time
    most_expensive: list[dict[str, Any]]
    least_used: list[dict[str, Any]]
    upcoming_renewals: list[dict[str, Any]]
    savings_opportunities: float
    average_subscription_cost: float


class CancellationReminderRequest(BaseModel):
    days_before: int = Field(ge=1, le=90)
    reason: str | None = None
    target_date: date | None = None


class CancellationReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    user_id: int
    reminder_date: date
    reason: str | None
    is_sent: bool
    created_at: datetime


class OptimizationSuggestion(BaseModel):
    subscription_id: int
    subscription_name: str
    suggestion_type: OptimizationSuggestionType
    current_cost: float
    potential_savings: float
    alternative_name: str | None
    alternative_cost: float | None
    reason: str
    confidence: float  # 0-1 score
    action_steps: list[str]


class OptimizationResponse(BaseModel):
    total_potential_savings: float
    suggestions: list[OptimizationSuggestion]
    bundling_opportunities: list[dict[str, Any]]
    unused_subscriptions: list[dict[str, Any]]
    duplicate_services: list[dict[str, Any]]
    optimization_score: float  # 0-100
    generated_at: datetime


# Additional request/response models for missing endpoints
class SubscriptionCreateRequest(BaseModel):
    service_name: str
    category: SubscriptionCategory
    amount: float
    billing_cycle: BillingCycle
    start_date: date | None = None
    payment_method_id: int | None = None
    auto_renew: bool | None = True
    description: str | None = None
    is_trial: bool | None = False
    trial_end_date: date | None = None
    regular_price: float | None = None
    shareable: bool | None = False
    max_users: int | None = 1


class SubscriptionDetailResponse(SubscriptionResponse):
    payment_history: list[dict[str, Any]]
    total_spent: float
    days_until_billing: int | None = None


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
    by_category: dict[str, float]


class PaymentHistoryResponse(BaseModel):
    amount: float
    payment_date: date
    status: str
    payment_method: str
    transaction_id: int | None = None


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
    duration_minutes: int | None = None
    notes: str | None = None


class SubscriptionUsageResponse(BaseModel):
    message: str


class SubscriptionRecommendationsResponse(BaseModel):
    unused_subscriptions: list[dict[str, Any]]
    duplicate_services: list[dict[str, Any]]
    savings_opportunities: list[dict[str, Any]]
    total_potential_savings: float


class SubscriptionShareRequest(BaseModel):
    share_with_username: str
    cost_split_percentage: float = Field(ge=0, le=100)


class SubscriptionShareResponse(BaseModel):
    id: int
    shared_users: list[dict[str, Any]]
    message: str


class BulkImportRequest(BaseModel):
    subscriptions: list[dict[str, Any]]


class BulkImportResponse(BaseModel):
    imported: int
    subscription_ids: list[int]
    errors: list[str] = []
