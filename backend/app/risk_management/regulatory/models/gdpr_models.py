"""GDPR Models - Data models for GDPR compliance management"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum


class LawfulBasis(str, Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTEREST = "vital_interest"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTEREST = "legitimate_interest"


class DataSubjectRight(str, Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    PORTABILITY = "portability"
    OBJECTION = "objection"
    AUTOMATED_DECISION = "automated_decision"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingActivity(BaseModel):
    activity_id: UUID = Field(default_factory=uuid4)
    activity_name: str
    description: str
    purpose: str
    lawful_basis: LawfulBasis
    data_categories: List[str]
    special_categories: List[str] = Field(default_factory=list)
    data_subjects: List[str]
    recipients: List[str]
    third_country_transfers: bool = False
    transfer_mechanism: Optional[str] = None
    retention_period: str
    technical_measures: List[str]
    organizational_measures: List[str]
    controller: str
    processor: Optional[str] = None
    dpo_review_date: Optional[date] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class ConsentRecord(BaseModel):
    consent_id: UUID = Field(default_factory=uuid4)
    data_subject_id: str
    purpose: str
    processing_activity_id: UUID
    consent_given: bool
    consent_date: datetime
    consent_method: str
    consent_text: str
    withdrawal_date: Optional[datetime] = None
    withdrawal_method: Optional[str] = None
    is_active: bool = True
    proof_location: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataSubjectRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    request_reference: str
    data_subject_id: str
    data_subject_email: str
    right_type: DataSubjectRight
    request_details: str
    received_date: datetime
    due_date: date
    status: str = "received"
    assigned_to: Optional[str] = None
    identity_verified: bool = False
    verification_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    response_details: Optional[str] = None
    extension_applied: bool = False
    extension_reason: Optional[str] = None
    completed_date: Optional[datetime] = None
    closed_by: Optional[str] = None


class DataBreach(BaseModel):
    breach_id: UUID = Field(default_factory=uuid4)
    breach_reference: str
    discovery_date: datetime
    occurrence_date: datetime
    breach_type: str
    severity: IncidentSeverity
    description: str
    data_categories_affected: List[str]
    special_categories_affected: List[str]
    number_of_records: int
    number_of_subjects: int
    systems_affected: List[str]
    root_cause: Optional[str] = None
    containment_measures: List[str]
    notification_required: bool = False
    dpa_notified: bool = False
    dpa_notification_date: Optional[datetime] = None
    subjects_notified: bool = False
    subjects_notification_date: Optional[datetime] = None
    risk_to_subjects: str
    corrective_actions: List[str]
    status: str = "investigating"
    closed_date: Optional[datetime] = None


class DataProtectionImpactAssessment(BaseModel):
    dpia_id: UUID = Field(default_factory=uuid4)
    dpia_reference: str
    project_name: str
    description: str
    processing_activity_id: Optional[UUID] = None
    necessity_assessment: str
    proportionality_assessment: str
    risks_identified: List[Dict[str, Any]]
    mitigation_measures: List[Dict[str, Any]]
    residual_risks: List[Dict[str, Any]]
    dpo_opinion: Optional[str] = None
    dpo_opinion_date: Optional[date] = None
    stakeholder_consultation: bool = False
    dpa_consultation_required: bool = False
    dpa_consultation_date: Optional[date] = None
    approved_by: Optional[str] = None
    approval_date: Optional[date] = None
    status: str = "draft"
    review_date: Optional[date] = None


class ThirdPartyDataTransfer(BaseModel):
    transfer_id: UUID = Field(default_factory=uuid4)
    data_exporter: str
    data_importer: str
    recipient_country: str
    is_adequate_country: bool
    transfer_mechanism: str  # SCC, BCR, consent, etc.
    data_categories: List[str]
    purposes: List[str]
    safeguards: List[str]
    supplementary_measures: List[str]
    tia_completed: bool = False  # Transfer Impact Assessment
    tia_date: Optional[date] = None
    contract_reference: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None
    is_active: bool = True


class GDPRComplianceReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_date: date
    reporting_period: str
    total_processing_activities: int
    activities_with_lawful_basis: int
    total_consent_records: int
    active_consents: int
    withdrawn_consents: int
    dsar_received: int
    dsar_completed: int
    dsar_avg_response_days: float
    breaches_reported: int
    breaches_notified_dpa: int
    dpias_completed: int
    third_country_transfers: int
    training_completed: int
    audit_findings: int
    open_remediation_items: int
    compliance_score: float
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
