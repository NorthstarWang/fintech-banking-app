from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Import shared enums from data_classes
from ..dto import (
    CreditScoreProvider, CreditScoreRange, CreditFactorType
)


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
    factors: List[Dict[str, Any]]


class CreditHistoryResponse(BaseModel):
    scores: List[Dict[str, Any]]  # List of score, date, provider
    average_score: float
    trend: str  # "improving", "declining", "stable"
    change_last_month: int
    change_last_year: int


class CreditSimulatorRequest(BaseModel):
    action_type: str  # "pay_off_debt", "open_new_card", "close_card", etc.
    action_details: Dict[str, Any]
    current_score: Optional[int] = None


class CreditSimulatorResponse(BaseModel):
    current_score: int
    projected_score: int
    score_change: int
    time_to_change_months: int
    impact_factors: List[Dict[str, Any]]
    recommendations: List[str]


class CreditTip(BaseModel):
    id: int
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    potential_score_impact: str
    category: CreditFactorType
    action_required: str


class CreditTipsResponse(BaseModel):
    tips: List[CreditTip]
    personalized: bool
    generated_at: datetime


class CreditReportResponse(BaseModel):
    report_id: str
    generated_at: datetime
    user_info: Dict[str, Any]
    credit_score: int
    accounts: List[Dict[str, Any]]
    payment_history: Dict[str, Any]
    credit_utilization: float
    credit_inquiries: List[Dict[str, Any]]
    public_records: List[Dict[str, Any]]
    collections: List[Dict[str, Any]]
    score_factors: List[Dict[str, Any]]