from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Import shared enums from data_classes
from ..dto import CreditFactorType, CreditScoreProvider, CreditScoreRange


# Request/Response Models
class CreditScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    score: int = Field(ge=300, le=850)
    provider: CreditScoreProvider
    score_range: CreditScoreRange
    last_updated: datetime
    next_update: datetime
    factors: list[dict[str, Any]]


class CreditHistoryResponse(BaseModel):
    scores: list[dict[str, Any]]  # List of score, date, provider
    average_score: float
    trend: str  # "improving", "declining", "stable"
    change_last_month: int
    change_last_year: int


class CreditSimulatorRequest(BaseModel):
    action_type: str  # "pay_off_debt", "open_new_card", "close_card", etc.
    action_details: dict[str, Any]
    current_score: int | None = None


class CreditSimulatorResponse(BaseModel):
    current_score: int
    projected_score: int
    score_change: int
    time_to_change_months: int
    impact_factors: list[dict[str, Any]]
    recommendations: list[str]


class CreditTip(BaseModel):
    id: int
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    potential_score_impact: str
    category: CreditFactorType
    action_required: str


class CreditTipsResponse(BaseModel):
    tips: list[CreditTip]
    personalized: bool
    generated_at: datetime


class CreditReportResponse(BaseModel):
    report_id: str
    generated_at: datetime
    user_info: dict[str, Any]
    credit_score: int
    accounts: list[dict[str, Any]]
    payment_history: dict[str, Any]
    credit_utilization: float
    credit_inquiries: list[dict[str, Any]]
    public_records: list[dict[str, Any]]
    collections: list[dict[str, Any]]
    score_factors: list[dict[str, Any]]
