"""Control Models - Data models for control management"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class ControlType(str, Enum):
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    DIRECTIVE = "directive"
    COMPENSATING = "compensating"


class ControlNature(str, Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    SEMI_AUTOMATED = "semi_automated"
    IT_DEPENDENT = "it_dependent"


class ControlCategory(str, Enum):
    AUTHORIZATION = "authorization"
    RECONCILIATION = "reconciliation"
    VERIFICATION = "verification"
    SEGREGATION = "segregation"
    PHYSICAL = "physical"
    MONITORING = "monitoring"
    SYSTEM = "system"


class ControlStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"
    REMEDIATION = "remediation"
    RETIRED = "retired"


class TestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


class Control(BaseModel):
    control_id: UUID = Field(default_factory=uuid4)
    control_code: str
    control_name: str
    control_description: str
    control_objective: str
    control_type: ControlType
    control_nature: ControlNature
    control_category: ControlCategory
    status: ControlStatus = ControlStatus.ACTIVE
    business_unit: str
    process: str
    owner: str
    frequency: str  # continuous, daily, weekly, monthly, etc.
    evidence_type: str
    evidence_location: str
    automation_level: int = 0  # 0-100%
    key_control: bool = False
    sox_control: bool = False
    regulatory_control: bool = False
    risks_mitigated: List[UUID] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)
    design_rating: Optional[str] = None
    operating_rating: Optional[str] = None
    overall_rating: Optional[str] = None
    last_test_date: Optional[date] = None
    next_test_date: Optional[date] = None
    created_date: date = Field(default_factory=date.today)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ControlTest(BaseModel):
    test_id: UUID = Field(default_factory=uuid4)
    control_id: UUID
    test_name: str
    test_type: str  # design, operating effectiveness
    test_date: date
    test_period_start: date
    test_period_end: date
    tester: str
    reviewer: Optional[str] = None
    sample_size: int
    population_size: int
    exceptions_found: int
    exception_rate: Decimal
    test_result: TestResult
    design_conclusion: Optional[str] = None
    operating_conclusion: Optional[str] = None
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    management_response: Optional[str] = None
    evidence_reviewed: List[str] = Field(default_factory=list)
    test_procedure: str
    notes: Optional[str] = None


class ControlException(BaseModel):
    exception_id: UUID = Field(default_factory=uuid4)
    control_id: UUID
    test_id: UUID
    exception_date: date
    exception_description: str
    root_cause: str
    impact: str
    severity: str  # high, medium, low
    compensating_control: Optional[str] = None
    remediation_required: bool = True
    remediation_action: Optional[str] = None
    remediation_owner: Optional[str] = None
    remediation_due_date: Optional[date] = None
    remediation_status: str = "open"
    remediation_completed_date: Optional[date] = None
    verified_by: Optional[str] = None
    verification_date: Optional[date] = None


class ControlGap(BaseModel):
    gap_id: UUID = Field(default_factory=uuid4)
    control_id: Optional[UUID] = None
    gap_type: str  # design, coverage, operating
    gap_description: str
    identified_date: date
    identified_by: str
    risk_exposure: str
    business_unit: str
    process: str
    severity: str
    remediation_plan: str
    remediation_owner: str
    target_remediation_date: date
    status: str = "open"
    actual_remediation_date: Optional[date] = None
    validation_required: bool = True
    validated_by: Optional[str] = None
    validation_date: Optional[date] = None


class ControlFramework(BaseModel):
    framework_id: UUID = Field(default_factory=uuid4)
    framework_name: str
    framework_version: str
    description: str
    issuing_body: str
    effective_date: date
    domains: List[str]
    total_controls: int
    applicable_controls: int
    implemented_controls: int
    implementation_percentage: Decimal
    last_assessment_date: Optional[date] = None
    next_assessment_date: Optional[date] = None
    is_active: bool = True


class ControlMapping(BaseModel):
    mapping_id: UUID = Field(default_factory=uuid4)
    control_id: UUID
    framework_id: UUID
    framework_control_id: str
    framework_control_name: str
    mapping_status: str  # full, partial, not_mapped
    mapping_notes: Optional[str] = None
    gap_identified: bool = False
    verified_by: Optional[str] = None
    verification_date: Optional[date] = None


class ControlMetrics(BaseModel):
    metrics_id: UUID = Field(default_factory=uuid4)
    metrics_date: date
    business_unit: Optional[str] = None
    total_controls: int
    active_controls: int
    key_controls: int
    automated_controls: int
    manual_controls: int
    controls_tested: int
    controls_passed: int
    controls_failed: int
    pass_rate: Decimal
    exception_count: int
    open_gaps: int
    overdue_remediations: int
    average_remediation_days: float
    sox_controls_count: int
    sox_controls_effective: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
