"""Rating Models - Credit rating and grading models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class RatingType(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    SHADOW = "shadow"
    BEHAVIORAL = "behavioral"


class RatingAgency(str, Enum):
    MOODYS = "moodys"
    SP = "sp"
    FITCH = "fitch"
    INTERNAL = "internal"


class RatingOutlook(str, Enum):
    POSITIVE = "positive"
    STABLE = "stable"
    NEGATIVE = "negative"
    DEVELOPING = "developing"


class CreditRating(BaseModel):
    rating_id: UUID = Field(default_factory=uuid4)
    entity_id: str
    entity_name: str
    entity_type: str  # customer, counterparty, obligor
    rating_type: RatingType
    rating_agency: RatingAgency
    rating_grade: str  # AAA, AA+, etc.
    rating_score: int = Field(ge=1, le=22)
    rating_category: str  # investment_grade, sub_investment_grade, default
    outlook: RatingOutlook = RatingOutlook.STABLE
    probability_of_default: float = Field(ge=0, le=1)
    loss_given_default: float = Field(ge=0, le=1)
    rating_date: date
    effective_date: date
    review_date: date
    expiry_date: Optional[date] = None
    previous_rating: Optional[str] = None
    rating_change: Optional[str] = None  # upgrade, downgrade, affirmed
    rating_factors: List[Dict[str, Any]] = []
    rating_rationale: str
    rated_by: str
    approved_by: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RatingScale(BaseModel):
    scale_id: UUID = Field(default_factory=uuid4)
    scale_name: str
    rating_agency: RatingAgency
    grades: List[Dict[str, Any]] = []
    default_grade: str
    pd_mapping: Dict[str, float] = {}
    lgd_mapping: Dict[str, float] = {}
    is_active: bool = True
    effective_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RatingGrade(BaseModel):
    grade_id: UUID = Field(default_factory=uuid4)
    scale_id: UUID
    grade_code: str
    grade_name: str
    grade_rank: int
    category: str
    pd_lower_bound: float
    pd_upper_bound: float
    pd_midpoint: float
    lgd_assumption: float
    risk_weight: float
    description: str


class RatingModel(BaseModel):
    model_id: UUID = Field(default_factory=uuid4)
    model_name: str
    model_type: str  # scorecard, statistical, expert
    entity_type: str
    segment: str
    version: str
    factors: List[Dict[str, Any]] = []
    factor_weights: Dict[str, float] = {}
    calibration_date: date
    validation_date: Optional[date] = None
    accuracy_metrics: Dict[str, float] = {}
    status: str = "active"
    created_by: str
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RatingMigration(BaseModel):
    migration_id: UUID = Field(default_factory=uuid4)
    entity_id: str
    entity_name: str
    from_rating: str
    to_rating: str
    migration_type: str  # upgrade, downgrade, default
    migration_date: date
    migration_reason: str
    trigger_events: List[str] = []
    migration_steps: int = 0
    previous_pd: float
    new_pd: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RatingReview(BaseModel):
    review_id: UUID = Field(default_factory=uuid4)
    rating_id: UUID
    entity_id: str
    review_type: str  # annual, trigger, interim
    review_date: date
    current_rating: str
    proposed_rating: str
    rating_action: str  # affirm, upgrade, downgrade, withdraw
    financial_analysis: Dict[str, Any] = {}
    qualitative_factors: Dict[str, Any] = {}
    industry_analysis: Dict[str, Any] = {}
    peer_comparison: Dict[str, Any] = {}
    recommendation: str
    reviewed_by: str
    review_notes: str
    status: str = "pending"
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RatingOverride(BaseModel):
    override_id: UUID = Field(default_factory=uuid4)
    rating_id: UUID
    entity_id: str
    model_rating: str
    override_rating: str
    override_reason: str
    override_type: str  # quantitative, qualitative, expert
    supporting_factors: List[str] = []
    override_date: date
    expiry_date: date
    approved_by: str
    approval_date: datetime
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RatingStatistics(BaseModel):
    total_ratings: int = 0
    by_grade: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_outlook: Dict[str, int] = {}
    upgrades_ytd: int = 0
    downgrades_ytd: int = 0
    defaults_ytd: int = 0
    average_pd: float = 0.0
