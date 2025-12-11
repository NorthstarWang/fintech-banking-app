"""
AML Case Models

Defines data structures for AML investigation cases.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class CaseStatus(str, Enum):
    """Case workflow status"""
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    PENDING_SAR = "pending_sar"
    SAR_FILED = "sar_filed"
    CLOSED_NO_ACTION = "closed_no_action"
    CLOSED_WITH_ACTION = "closed_with_action"


class CasePriority(str, Enum):
    """Case priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CaseCategory(str, Enum):
    """Case categories"""
    MONEY_LAUNDERING = "money_laundering"
    TERRORIST_FINANCING = "terrorist_financing"
    FRAUD = "fraud"
    SANCTIONS_VIOLATION = "sanctions_violation"
    TAX_EVASION = "tax_evasion"
    BRIBERY_CORRUPTION = "bribery_corruption"
    STRUCTURING = "structuring"
    UNKNOWN_SOURCE_OF_FUNDS = "unknown_source_of_funds"
    SHELL_COMPANY = "shell_company"
    OTHER = "other"


class InvestigationFinding(BaseModel):
    """Individual investigation finding"""
    finding_id: UUID = Field(default_factory=uuid4)
    finding_type: str
    description: str
    severity: str
    evidence_refs: List[UUID] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    validated: bool = False
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None


class CaseTimeline(BaseModel):
    """Timeline entry for case activity"""
    entry_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    activity_type: str
    description: str
    actor_id: str
    actor_name: str
    details: Dict[str, Any] = Field(default_factory=dict)


class CaseDocument(BaseModel):
    """Document attached to a case"""
    document_id: UUID = Field(default_factory=uuid4)
    document_name: str
    document_type: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RelatedEntity(BaseModel):
    """Entity related to a case"""
    entity_id: str
    entity_type: str  # customer, account, transaction, organization
    entity_name: str
    relationship_type: str
    added_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class CaseAssignment(BaseModel):
    """Case assignment record"""
    assignment_id: UUID = Field(default_factory=uuid4)
    assigned_to: str
    assigned_by: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    role: str
    is_primary: bool = False
    notes: Optional[str] = None


class SARReference(BaseModel):
    """SAR filing reference"""
    sar_id: UUID
    sar_number: str
    filing_date: datetime
    filing_status: str
    acknowledgment_number: Optional[str] = None


class AMLCase(BaseModel):
    """Main AML Investigation Case entity"""
    case_id: UUID = Field(default_factory=uuid4)
    case_number: str
    title: str
    description: str

    # Classification
    status: CaseStatus = CaseStatus.DRAFT
    priority: CasePriority = CasePriority.MEDIUM
    category: CaseCategory
    subcategory: Optional[str] = None

    # Subject information
    primary_subject_id: str
    primary_subject_type: str
    primary_subject_name: str

    # Related entities
    related_entities: List[RelatedEntity] = Field(default_factory=list)

    # Alerts linked to this case
    alert_ids: List[UUID] = Field(default_factory=list)

    # Financial summary
    total_suspicious_amount: float = 0.0
    transaction_count: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    currencies_involved: List[str] = Field(default_factory=list)
    countries_involved: List[str] = Field(default_factory=list)

    # Investigation
    findings: List[InvestigationFinding] = Field(default_factory=list)
    timeline: List[CaseTimeline] = Field(default_factory=list)
    documents: List[CaseDocument] = Field(default_factory=list)

    # Assignment
    assignments: List[CaseAssignment] = Field(default_factory=list)
    lead_investigator: Optional[str] = None
    review_team: List[str] = Field(default_factory=list)

    # SAR information
    sar_required: bool = False
    sar_deadline: Optional[datetime] = None
    sar_references: List[SARReference] = Field(default_factory=list)

    # Risk assessment
    initial_risk_score: float = 0.0
    current_risk_score: float = 0.0
    risk_factors: List[str] = Field(default_factory=list)

    # Resolution
    resolution_type: Optional[str] = None
    resolution_summary: Optional[str] = None
    resolved_by: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    # Metadata
    source_system: str = "aml_case_management"
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseSummary(BaseModel):
    """Summarized view of a case for listings"""
    case_id: UUID
    case_number: str
    title: str
    status: CaseStatus
    priority: CasePriority
    category: CaseCategory
    primary_subject_name: str
    alert_count: int
    total_suspicious_amount: float
    lead_investigator: Optional[str] = None
    created_at: datetime
    due_date: Optional[datetime] = None
    sar_required: bool


class CaseStatistics(BaseModel):
    """Case statistics for dashboards"""
    total_cases: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)
    average_resolution_days: float = 0.0
    sar_filing_rate: float = 0.0
    overdue_count: int = 0
    open_cases: int = 0
    closed_this_month: int = 0
    avg_alerts_per_case: float = 0.0


class CaseCreateRequest(BaseModel):
    """Request model for creating a case"""
    title: str
    description: str
    category: CaseCategory
    priority: CasePriority = CasePriority.MEDIUM
    primary_subject_id: str
    primary_subject_type: str
    primary_subject_name: str
    alert_ids: List[UUID] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class CaseUpdateRequest(BaseModel):
    """Request model for updating a case"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    category: Optional[CaseCategory] = None
    lead_investigator: Optional[str] = None
    sar_required: Optional[bool] = None
    sar_deadline: Optional[datetime] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class CaseSearchCriteria(BaseModel):
    """Search criteria for cases"""
    statuses: Optional[List[CaseStatus]] = None
    priorities: Optional[List[CasePriority]] = None
    categories: Optional[List[CaseCategory]] = None
    investigators: Optional[List[str]] = None
    subject_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    sar_required: Optional[bool] = None
    overdue_only: bool = False
    tags: Optional[List[str]] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"
