"""KRI Models - Key Risk Indicator data models"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class KRIType(str, Enum):
    LEADING = "leading"
    LAGGING = "lagging"
    CONCURRENT = "concurrent"


class KRICategory(str, Enum):
    OPERATIONAL = "operational"
    CREDIT = "credit"
    MARKET = "market"
    LIQUIDITY = "liquidity"
    COMPLIANCE = "compliance"
    TECHNOLOGY = "technology"
    PEOPLE = "people"
    PROCESS = "process"


class ThresholdStatus(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class KRITrend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"


class KeyRiskIndicator(BaseModel):
    kri_id: UUID = Field(default_factory=uuid4)
    kri_code: str
    kri_name: str
    description: str
    kri_type: KRIType
    category: KRICategory
    business_unit: str
    owner: str
    measurement_unit: str
    measurement_frequency: str  # daily, weekly, monthly, quarterly
    data_source: str
    calculation_method: str
    green_threshold_min: Optional[Decimal] = None
    green_threshold_max: Optional[Decimal] = None
    amber_threshold_min: Optional[Decimal] = None
    amber_threshold_max: Optional[Decimal] = None
    red_threshold_min: Optional[Decimal] = None
    red_threshold_max: Optional[Decimal] = None
    higher_is_worse: bool = True
    related_risks: List[UUID] = Field(default_factory=list)
    is_active: bool = True
    created_date: date = Field(default_factory=date.today)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KRIMeasurement(BaseModel):
    measurement_id: UUID = Field(default_factory=uuid4)
    kri_id: UUID
    measurement_date: date
    measurement_period: str
    value: Decimal
    previous_value: Optional[Decimal] = None
    threshold_status: ThresholdStatus
    trend: KRITrend
    variance_from_target: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    breach_occurred: bool = False
    breach_type: Optional[str] = None
    data_quality_flag: bool = False
    notes: Optional[str] = None
    recorded_by: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class KRIThresholdBreach(BaseModel):
    breach_id: UUID = Field(default_factory=uuid4)
    kri_id: UUID
    measurement_id: UUID
    breach_date: date
    breach_type: str  # amber, red
    breach_value: Decimal
    threshold_breached: Decimal
    breach_duration: Optional[int] = None  # days
    escalated: bool = False
    escalation_date: Optional[datetime] = None
    escalated_to: Optional[str] = None
    action_taken: Optional[str] = None
    resolution_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    status: str = "open"


class KRITarget(BaseModel):
    target_id: UUID = Field(default_factory=uuid4)
    kri_id: UUID
    target_period: str
    target_value: Decimal
    target_type: str  # absolute, percentage, range
    effective_from: date
    effective_to: Optional[date] = None
    approved_by: str
    approval_date: date
    rationale: Optional[str] = None
    is_active: bool = True


class KRITrendAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    kri_id: UUID
    analysis_date: date
    analysis_period: str
    period_start: date
    period_end: date
    data_points: int
    average_value: Decimal
    min_value: Decimal
    max_value: Decimal
    standard_deviation: Decimal
    trend_direction: KRITrend
    trend_coefficient: Decimal
    green_percentage: Decimal
    amber_percentage: Decimal
    red_percentage: Decimal
    breach_count: int
    volatility: Decimal
    forecast_next_period: Optional[Decimal] = None


class KRIDashboard(BaseModel):
    dashboard_id: UUID = Field(default_factory=uuid4)
    dashboard_date: date
    business_unit: Optional[str] = None
    total_kris: int
    active_kris: int
    green_count: int
    amber_count: int
    red_count: int
    breaches_this_period: int
    improving_count: int
    stable_count: int
    deteriorating_count: int
    data_quality_issues: int
    kri_summary: List[Dict[str, Any]]
    top_concerns: List[Dict[str, Any]]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class KRIReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_date: date
    report_type: str
    period: str
    period_start: date
    period_end: date
    business_unit: Optional[str] = None
    kri_count: int
    measurements_count: int
    status_distribution: Dict[str, int]
    trend_distribution: Dict[str, int]
    total_breaches: int
    amber_breaches: int
    red_breaches: int
    average_breach_duration: float
    escalation_count: int
    resolution_rate: Decimal
    top_breached_kris: List[Dict[str, Any]]
    generated_by: str
