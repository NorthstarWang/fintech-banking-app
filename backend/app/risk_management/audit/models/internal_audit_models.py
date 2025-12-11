"""Internal Audit Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class AuditType(str, Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    IT = "it"
    INTEGRATED = "integrated"
    SPECIAL = "special"
    FOLLOW_UP = "follow_up"


class AuditStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    FIELDWORK = "fieldwork"
    REPORTING = "reporting"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ADVISORY = "advisory"


class InternalAudit(BaseModel):
    audit_id: UUID = Field(default_factory=uuid4)
    audit_reference: str
    audit_name: str
    audit_type: AuditType
    audit_scope: str
    audit_objectives: List[str]
    business_unit: str
    audit_period_start: date
    audit_period_end: date
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    lead_auditor: str
    audit_team: List[str]
    status: AuditStatus = AuditStatus.PLANNED
    risk_rating: str = "medium"
    budgeted_hours: int = 0
    actual_hours: int = 0
    methodology: str = ""
    created_date: datetime = Field(default_factory=datetime.utcnow)


class AuditWorkpaper(BaseModel):
    workpaper_id: UUID = Field(default_factory=uuid4)
    audit_id: UUID
    workpaper_reference: str
    workpaper_title: str
    workpaper_type: str
    section: str
    prepared_by: str
    prepared_date: date
    reviewed_by: Optional[str] = None
    review_date: Optional[date] = None
    status: str = "draft"
    description: str = ""
    testing_objective: str = ""
    testing_procedure: str = ""
    sample_size: int = 0
    population_size: int = 0
    exceptions_found: int = 0
    conclusion: str = ""
    attachments: List[str] = Field(default_factory=list)


class AuditFinding(BaseModel):
    finding_id: UUID = Field(default_factory=uuid4)
    audit_id: UUID
    finding_reference: str
    finding_title: str
    severity: FindingSeverity
    condition: str
    criteria: str
    cause: str
    effect: str
    recommendation: str
    management_response: str = ""
    action_plan: str = ""
    action_owner: str = ""
    target_date: Optional[date] = None
    status: str = "open"
    validated: bool = False
    validation_date: Optional[date] = None
    validated_by: Optional[str] = None
    repeat_finding: bool = False
    prior_finding_reference: Optional[str] = None


class AuditReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    audit_id: UUID
    report_reference: str
    report_title: str
    report_type: str
    executive_summary: str
    scope_summary: str
    methodology_summary: str
    findings_summary: Dict[str, int] = Field(default_factory=dict)
    overall_opinion: str
    key_observations: List[str] = Field(default_factory=list)
    positive_observations: List[str] = Field(default_factory=list)
    drafted_by: str
    drafted_date: date
    reviewed_by: Optional[str] = None
    review_date: Optional[date] = None
    approved_by: Optional[str] = None
    approval_date: Optional[date] = None
    issued_date: Optional[date] = None
    distribution_list: List[str] = Field(default_factory=list)
    status: str = "draft"


class AuditFollowUp(BaseModel):
    follow_up_id: UUID = Field(default_factory=uuid4)
    finding_id: UUID
    audit_id: UUID
    follow_up_date: date
    follow_up_by: str
    implementation_status: str
    evidence_reviewed: List[str] = Field(default_factory=list)
    management_update: str = ""
    auditor_assessment: str = ""
    remaining_risk: str = ""
    revised_target_date: Optional[date] = None
    closed: bool = False
    closed_date: Optional[date] = None
