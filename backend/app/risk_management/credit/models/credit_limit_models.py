"""Credit Limit Models - Credit limit management models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class LimitType(str, Enum):
    CUSTOMER = "customer"
    GROUP = "group"
    PRODUCT = "product"
    INDUSTRY = "industry"
    COUNTRY = "country"
    CURRENCY = "currency"
    TENOR = "tenor"


class LimitStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING_APPROVAL = "pending_approval"
    CANCELLED = "cancelled"


class UtilizationStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    BREACH = "breach"
    EXCESS = "excess"


class CreditLimit(BaseModel):
    limit_id: UUID = Field(default_factory=uuid4)
    limit_number: str
    limit_type: LimitType
    entity_id: str
    entity_name: str
    limit_amount: float
    currency: str = "USD"
    utilized_amount: float = 0.0
    available_amount: float
    utilization_percentage: float = 0.0
    warning_threshold: float = 80.0
    breach_threshold: float = 100.0
    utilization_status: UtilizationStatus = UtilizationStatus.NORMAL
    status: LimitStatus = LimitStatus.ACTIVE
    effective_date: date
    expiry_date: date
    review_date: date
    approved_by: str
    approved_date: datetime
    approval_authority: str
    conditions: List[str] = []
    covenants: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LimitRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    request_number: str
    request_type: str  # new, increase, decrease, renewal, cancellation
    limit_type: LimitType
    entity_id: str
    entity_name: str
    current_limit: Optional[float] = None
    requested_limit: float
    requested_tenor_months: int
    purpose: str
    justification: str
    supporting_documents: List[str] = []
    risk_assessment: Optional[Dict[str, Any]] = None
    credit_rating: Optional[str] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    requested_by: str
    request_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
    current_approver: Optional[str] = None
    approval_history: List[Dict[str, Any]] = []
    decision: Optional[str] = None
    decision_date: Optional[datetime] = None
    approved_amount: Optional[float] = None
    conditions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LimitUtilization(BaseModel):
    utilization_id: UUID = Field(default_factory=uuid4)
    limit_id: UUID
    facility_id: Optional[UUID] = None
    utilization_date: date
    utilized_amount: float
    utilization_type: str  # drawdown, repayment, adjustment
    transaction_reference: Optional[str] = None
    balance_after: float
    utilization_percentage_after: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LimitReview(BaseModel):
    review_id: UUID = Field(default_factory=uuid4)
    limit_id: UUID
    review_date: date
    review_type: str  # annual, trigger, interim
    current_limit: float
    recommended_limit: float
    limit_change: float
    change_reason: str
    financial_performance: Dict[str, Any] = {}
    risk_assessment: Dict[str, Any] = {}
    covenant_compliance: Dict[str, Any] = {}
    industry_outlook: str
    recommendation: str
    reviewed_by: str
    approved_by: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LimitBreach(BaseModel):
    breach_id: UUID = Field(default_factory=uuid4)
    limit_id: UUID
    breach_date: datetime
    breach_type: str  # limit, warning, covenant
    limit_amount: float
    utilized_amount: float
    breach_amount: float
    breach_percentage: float
    breach_reason: str
    transaction_id: Optional[str] = None
    remediation_required: bool = True
    remediation_plan: Optional[str] = None
    remediation_deadline: Optional[date] = None
    resolved: bool = False
    resolved_date: Optional[datetime] = None
    resolution_action: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LimitCovenant(BaseModel):
    covenant_id: UUID = Field(default_factory=uuid4)
    limit_id: UUID
    covenant_type: str  # financial, reporting, negative
    covenant_name: str
    covenant_description: str
    threshold_value: float
    current_value: Optional[float] = None
    compliance_status: str = "compliant"
    measurement_frequency: str  # monthly, quarterly, annually
    last_measurement_date: Optional[date] = None
    next_measurement_date: Optional[date] = None
    grace_period_days: int = 0
    breach_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LimitStatistics(BaseModel):
    total_limits: int = 0
    total_limit_amount: float = 0.0
    total_utilized: float = 0.0
    average_utilization: float = 0.0
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    breaches_count: int = 0
    warnings_count: int = 0
