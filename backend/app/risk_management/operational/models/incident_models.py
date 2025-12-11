"""Incident Models - Data models for operational incident management"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class IncidentCategory(str, Enum):
    OPERATIONAL = "operational"
    TECHNOLOGY = "technology"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    FRAUD = "fraud"
    PROCESS_FAILURE = "process_failure"
    HUMAN_ERROR = "human_error"
    EXTERNAL_EVENT = "external_event"
    VENDOR = "vendor"


class IncidentImpact(str, Enum):
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"
    REGULATORY = "regulatory"
    CUSTOMER = "customer"
    OPERATIONAL = "operational"
    LEGAL = "legal"


class Incident(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    incident_number: str
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    reported_by: str
    reported_date: datetime = Field(default_factory=datetime.utcnow)
    occurred_date: datetime
    detected_date: datetime
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    business_unit: str
    affected_systems: List[str] = Field(default_factory=list)
    impact_types: List[IncidentImpact] = Field(default_factory=list)
    estimated_loss: Optional[Decimal] = None
    actual_loss: Optional[Decimal] = None
    root_cause: Optional[str] = None
    remediation_actions: List[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    escalated: bool = False
    escalation_level: int = 0
    regulatory_reportable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentTimeline(BaseModel):
    timeline_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    event_time: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    description: str
    performed_by: str
    old_status: Optional[IncidentStatus] = None
    new_status: Optional[IncidentStatus] = None
    attachments: List[str] = Field(default_factory=list)


class IncidentEscalation(BaseModel):
    escalation_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    escalation_level: int
    escalated_to: str
    escalated_by: str
    escalation_time: datetime = Field(default_factory=datetime.utcnow)
    reason: str
    acknowledged: bool = False
    acknowledged_time: Optional[datetime] = None


class IncidentRootCauseAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    analysis_date: date
    analyst: str
    root_causes: List[str]
    contributing_factors: List[str]
    methodology: str  # 5 Whys, Fishbone, etc.
    findings: str
    recommendations: List[str]
    preventive_measures: List[str]
    status: str = "draft"
    approved_by: Optional[str] = None
    approval_date: Optional[date] = None


class IncidentCorrectiveAction(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    analysis_id: Optional[UUID] = None
    action_type: str  # immediate, short_term, long_term
    description: str
    assigned_to: str
    due_date: date
    status: str = "pending"
    completion_date: Optional[date] = None
    verification_required: bool = True
    verified_by: Optional[str] = None
    verification_date: Optional[date] = None
    effectiveness_rating: Optional[int] = None


class IncidentReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_date: date
    report_type: str  # daily, weekly, monthly
    period_start: date
    period_end: date
    total_incidents: int
    incidents_by_severity: Dict[str, int]
    incidents_by_category: Dict[str, int]
    incidents_by_status: Dict[str, int]
    total_estimated_loss: Decimal
    total_actual_loss: Decimal
    average_resolution_time: float  # hours
    escalation_rate: float
    trending_categories: List[str]
    generated_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
