"""Issue Management Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class IssueSource(str, Enum):
    INTERNAL_AUDIT = "internal_audit"
    EXTERNAL_AUDIT = "external_audit"
    REGULATORY_EXAM = "regulatory_exam"
    SELF_IDENTIFIED = "self_identified"
    COMPLIANCE_TESTING = "compliance_testing"
    INCIDENT = "incident"
    CUSTOMER_COMPLAINT = "customer_complaint"
    RISK_ASSESSMENT = "risk_assessment"


class IssuePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    CLOSED = "closed"
    OVERDUE = "overdue"
    ESCALATED = "escalated"


class Issue(BaseModel):
    issue_id: UUID = Field(default_factory=uuid4)
    issue_reference: str
    issue_title: str
    source: IssueSource
    source_reference: str = ""
    priority: IssuePriority
    description: str
    root_cause: str = ""
    impact: str
    risk_rating: str = "medium"
    business_unit: str
    process_affected: str = ""
    identified_date: date
    identified_by: str
    owner: str
    due_date: date
    extended_due_date: Optional[date] = None
    extension_count: int = 0
    status: IssueStatus = IssueStatus.OPEN
    created_date: datetime = Field(default_factory=datetime.utcnow)


class ActionPlan(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    issue_id: UUID
    action_reference: str
    action_description: str
    action_type: str
    owner: str
    due_date: date
    completion_date: Optional[date] = None
    status: str = "open"
    progress_percentage: int = 0
    evidence_required: List[str] = Field(default_factory=list)
    evidence_provided: List[str] = Field(default_factory=list)
    comments: str = ""
    dependencies: List[str] = Field(default_factory=list)


class IssueUpdate(BaseModel):
    update_id: UUID = Field(default_factory=uuid4)
    issue_id: UUID
    update_date: date
    updated_by: str
    update_type: str  # progress, status_change, extension, escalation
    previous_status: str = ""
    new_status: str = ""
    progress_update: str
    blockers: List[str] = Field(default_factory=list)
    next_steps: str = ""
    documents_attached: List[str] = Field(default_factory=list)


class IssueValidation(BaseModel):
    validation_id: UUID = Field(default_factory=uuid4)
    issue_id: UUID
    validation_date: date
    validator: str
    validation_type: str  # initial, follow_up, final
    evidence_reviewed: List[str] = Field(default_factory=list)
    tests_performed: List[str] = Field(default_factory=list)
    validation_result: str  # validated, not_validated, partial
    findings: str = ""
    remaining_risk: str = ""
    recommendation: str = ""
    reopen_required: bool = False


class IssueEscalation(BaseModel):
    escalation_id: UUID = Field(default_factory=uuid4)
    issue_id: UUID
    escalation_date: date
    escalated_by: str
    escalation_reason: str
    escalated_to: str
    escalation_level: int
    response_required_by: date
    response_received: Optional[str] = None
    response_date: Optional[date] = None
    resolution: str = ""
    status: str = "pending"


class IssueReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_period: str
    report_date: date
    prepared_by: str
    total_issues: int = 0
    issues_by_source: Dict[str, int] = Field(default_factory=dict)
    issues_by_priority: Dict[str, int] = Field(default_factory=dict)
    issues_by_status: Dict[str, int] = Field(default_factory=dict)
    opened_this_period: int = 0
    closed_this_period: int = 0
    overdue_issues: int = 0
    aging_analysis: Dict[str, int] = Field(default_factory=dict)
    key_issues: List[Dict[str, Any]] = Field(default_factory=list)
    trends: Dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"
