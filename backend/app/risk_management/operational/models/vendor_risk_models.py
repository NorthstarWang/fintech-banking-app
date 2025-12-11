"""Vendor Risk Models - Data models for third-party risk management"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class VendorTier(str, Enum):
    TIER_1 = "tier_1"  # Critical
    TIER_2 = "tier_2"  # High
    TIER_3 = "tier_3"  # Medium
    TIER_4 = "tier_4"  # Low


class VendorStatus(str, Enum):
    PROSPECTIVE = "prospective"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    UNDER_REVIEW = "under_review"
    TERMINATED = "terminated"
    BLOCKED = "blocked"


class ServiceCategory(str, Enum):
    TECHNOLOGY = "technology"
    FINANCIAL = "financial"
    PROFESSIONAL = "professional"
    OPERATIONAL = "operational"
    FACILITIES = "facilities"
    MARKETING = "marketing"
    LEGAL = "legal"
    HR = "hr"


class RiskRating(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssessmentType(str, Enum):
    INITIAL = "initial"
    PERIODIC = "periodic"
    AD_HOC = "ad_hoc"
    INCIDENT = "incident"
    EXIT = "exit"


class Vendor(BaseModel):
    vendor_id: UUID = Field(default_factory=uuid4)
    vendor_code: str
    vendor_name: str
    legal_name: str
    dba_name: Optional[str] = None
    vendor_tier: VendorTier
    status: VendorStatus = VendorStatus.PROSPECTIVE
    service_category: ServiceCategory
    services_provided: List[str]
    primary_contact: str
    contact_email: str
    contact_phone: str
    address: str
    country: str
    tax_id: Optional[str] = None
    duns_number: Optional[str] = None
    relationship_owner: str
    business_unit: str
    onboarding_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    annual_spend: Decimal = Decimal("0")
    payment_terms: str
    overall_risk_rating: Optional[RiskRating] = None
    last_assessment_date: Optional[date] = None
    next_assessment_date: Optional[date] = None
    data_access: bool = False
    pii_access: bool = False
    system_access: bool = False
    critical_vendor: bool = False
    concentration_risk: bool = False
    subcontractors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VendorContract(BaseModel):
    contract_id: UUID = Field(default_factory=uuid4)
    vendor_id: UUID
    contract_number: str
    contract_name: str
    contract_type: str
    effective_date: date
    expiration_date: date
    auto_renewal: bool = False
    renewal_notice_days: int = 90
    contract_value: Decimal
    currency: str
    payment_frequency: str
    sla_attached: bool = False
    nda_attached: bool = False
    insurance_required: bool = False
    insurance_verified: bool = False
    audit_rights: bool = False
    termination_notice_days: int
    termination_for_cause: bool = True
    termination_for_convenience: bool = False
    data_protection_clause: bool = False
    subcontracting_allowed: bool = False
    status: str = "active"
    owner: str
    approved_by: str
    approval_date: date
    document_location: str


class VendorAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    vendor_id: UUID
    assessment_type: AssessmentType
    assessment_date: date
    assessor: str
    reviewer: Optional[str] = None
    status: str = "in_progress"
    financial_risk_rating: RiskRating
    operational_risk_rating: RiskRating
    compliance_risk_rating: RiskRating
    security_risk_rating: RiskRating
    reputational_risk_rating: RiskRating
    overall_risk_rating: RiskRating
    inherent_risk_score: int
    residual_risk_score: int
    financial_stability: str
    years_in_business: int
    certifications: List[str]
    audit_reports: List[str]
    insurance_coverage: Dict[str, Decimal]
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    approved_by: Optional[str] = None
    approval_date: Optional[date] = None


class VendorDueDiligence(BaseModel):
    due_diligence_id: UUID = Field(default_factory=uuid4)
    vendor_id: UUID
    due_diligence_type: str
    request_date: date
    completion_date: Optional[date] = None
    status: str = "pending"
    background_check: bool = False
    financial_review: bool = False
    reference_check: bool = False
    site_visit: bool = False
    security_assessment: bool = False
    compliance_verification: bool = False
    sanctions_screening: bool = False
    adverse_media_check: bool = False
    findings: Dict[str, Any] = Field(default_factory=dict)
    risk_flags: List[str] = Field(default_factory=list)
    recommendation: str = ""
    performed_by: str
    reviewed_by: Optional[str] = None


class VendorIncident(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    vendor_id: UUID
    incident_date: datetime
    reported_date: datetime
    incident_type: str
    severity: str
    description: str
    impact_description: str
    service_affected: str
    root_cause: Optional[str] = None
    vendor_response: Optional[str] = None
    remediation_actions: List[str] = Field(default_factory=list)
    remediation_deadline: Optional[date] = None
    status: str = "open"
    resolution_date: Optional[datetime] = None
    financial_impact: Optional[Decimal] = None
    sla_breached: bool = False
    credit_applied: Optional[Decimal] = None
    escalated: bool = False
    regulatory_notification: bool = False


class VendorPerformance(BaseModel):
    performance_id: UUID = Field(default_factory=uuid4)
    vendor_id: UUID
    review_period: str
    period_start: date
    period_end: date
    sla_metrics: Dict[str, Decimal]
    overall_sla_compliance: Decimal
    quality_score: Decimal
    delivery_score: Decimal
    responsiveness_score: Decimal
    cost_performance: Decimal
    overall_score: Decimal
    issues_reported: int
    issues_resolved: int
    incidents_count: int
    strengths: List[str]
    areas_for_improvement: List[str]
    action_items: List[Dict[str, Any]]
    reviewer: str
    review_date: date


class VendorRiskMetrics(BaseModel):
    metrics_id: UUID = Field(default_factory=uuid4)
    metrics_date: date
    total_vendors: int
    active_vendors: int
    critical_vendors: int
    tier_1_count: int
    tier_2_count: int
    tier_3_count: int
    tier_4_count: int
    high_risk_vendors: int
    total_spend: Decimal
    assessments_due: int
    assessments_overdue: int
    contracts_expiring_90_days: int
    open_incidents: int
    average_performance_score: Decimal
    concentration_risk_vendors: int
    data_access_vendors: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
