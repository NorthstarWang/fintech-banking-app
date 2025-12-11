"""RCSA Models - Risk Control Self-Assessment data models"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class RiskCategory(str, Enum):
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    TECHNOLOGY = "technology"
    REPUTATIONAL = "reputational"
    LEGAL = "legal"


class RiskLikelihood(str, Enum):
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class RiskImpact(str, Enum):
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class ControlEffectiveness(str, Enum):
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    NOT_TESTED = "not_tested"


class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    EXPIRED = "expired"


class RCSAAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    assessment_name: str
    business_unit: str
    process_name: str
    process_owner: str
    assessment_date: date
    due_date: date
    status: AssessmentStatus = AssessmentStatus.DRAFT
    assessor: str
    reviewer: Optional[str] = None
    approver: Optional[str] = None
    review_date: Optional[date] = None
    approval_date: Optional[date] = None
    next_assessment_date: Optional[date] = None
    overall_risk_rating: Optional[str] = None
    overall_control_rating: Optional[str] = None
    total_risks_identified: int = 0
    total_controls_assessed: int = 0
    action_items_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RCSARisk(BaseModel):
    risk_id: UUID = Field(default_factory=uuid4)
    assessment_id: UUID
    risk_reference: str
    risk_name: str
    risk_description: str
    risk_category: RiskCategory
    risk_owner: str
    inherent_likelihood: RiskLikelihood
    inherent_impact: RiskImpact
    inherent_risk_score: int
    inherent_risk_rating: str
    residual_likelihood: RiskLikelihood
    residual_impact: RiskImpact
    residual_risk_score: int
    residual_risk_rating: str
    target_likelihood: Optional[RiskLikelihood] = None
    target_impact: Optional[RiskImpact] = None
    target_risk_score: Optional[int] = None
    risk_appetite: str
    within_appetite: bool = True
    trend: str = "stable"  # increasing, stable, decreasing
    controls_mapped: List[UUID] = Field(default_factory=list)
    action_required: bool = False


class RCSAControl(BaseModel):
    control_id: UUID = Field(default_factory=uuid4)
    assessment_id: UUID
    control_reference: str
    control_name: str
    control_description: str
    control_type: str  # preventive, detective, corrective
    control_nature: str  # manual, automated, semi-automated
    control_owner: str
    frequency: str
    design_effectiveness: ControlEffectiveness
    operating_effectiveness: ControlEffectiveness
    overall_effectiveness: ControlEffectiveness
    last_test_date: Optional[date] = None
    next_test_date: Optional[date] = None
    test_results: Optional[str] = None
    risks_mitigated: List[UUID] = Field(default_factory=list)
    gaps_identified: List[str] = Field(default_factory=list)
    improvement_required: bool = False


class RCSAActionItem(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    assessment_id: UUID
    risk_id: Optional[UUID] = None
    control_id: Optional[UUID] = None
    action_type: str  # risk_mitigation, control_improvement, gap_remediation
    action_description: str
    assigned_to: str
    due_date: date
    priority: str  # high, medium, low
    status: str = "open"
    completion_date: Optional[date] = None
    verification_required: bool = True
    verified_by: Optional[str] = None
    verification_date: Optional[date] = None
    notes: Optional[str] = None


class RiskHeatmap(BaseModel):
    heatmap_id: UUID = Field(default_factory=uuid4)
    assessment_id: Optional[UUID] = None
    generated_date: date
    heatmap_type: str  # inherent, residual
    business_unit: Optional[str] = None
    matrix_data: List[List[int]]  # 5x5 matrix with counts
    risk_distribution: Dict[str, int]
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_risks: int


class RCSAReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_date: date
    report_type: str
    period: str
    business_unit: Optional[str] = None
    assessments_completed: int
    assessments_pending: int
    total_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    risks_outside_appetite: int
    total_controls: int
    effective_controls: int
    partially_effective_controls: int
    ineffective_controls: int
    open_action_items: int
    overdue_action_items: int
    generated_by: str
