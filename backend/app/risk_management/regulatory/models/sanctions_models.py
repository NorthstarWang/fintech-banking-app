"""Sanctions Models - Data models for sanctions compliance"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class SanctionsList(str, Enum):
    OFAC_SDN = "ofac_sdn"
    OFAC_SSI = "ofac_ssi"
    OFAC_CAPTA = "ofac_capta"
    UN_CONSOLIDATED = "un_consolidated"
    EU_CONSOLIDATED = "eu_consolidated"
    UK_CONSOLIDATED = "uk_consolidated"
    FATF = "fatf"


class ScreeningType(str, Enum):
    NAME = "name"
    TRANSACTION = "transaction"
    PAYMENT = "payment"
    ONBOARDING = "onboarding"
    PERIODIC = "periodic"


class AlertStatus(str, Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    ESCALATED = "escalated"
    TRUE_MATCH = "true_match"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class MatchStrength(str, Enum):
    EXACT = "exact"
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


class SanctionsListEntry(BaseModel):
    entry_id: UUID = Field(default_factory=uuid4)
    list_source: SanctionsList
    list_entry_id: str
    entry_type: str  # individual, entity, vessel, aircraft
    name: str
    aliases: List[str] = Field(default_factory=list)
    date_of_birth: Optional[date] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    passport_numbers: List[str] = Field(default_factory=list)
    id_numbers: List[str] = Field(default_factory=list)
    addresses: List[str] = Field(default_factory=list)
    programs: List[str] = Field(default_factory=list)
    sanctions_type: str
    listed_date: date
    delisted_date: Optional[date] = None
    remarks: Optional[str] = None
    is_active: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ScreeningRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    screening_type: ScreeningType
    request_reference: str
    screening_date: datetime = Field(default_factory=datetime.utcnow)
    requestor: str
    lists_screened: List[SanctionsList]
    subject_type: str
    subject_name: str
    subject_dob: Optional[date] = None
    subject_country: Optional[str] = None
    subject_id: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    matches_found: int = 0
    status: str = "pending"
    completed_date: Optional[datetime] = None
    processing_time_ms: Optional[int] = None


class ScreeningAlert(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    alert_reference: str
    list_source: SanctionsList
    list_entry_id: str
    matched_name: str
    subject_name: str
    match_strength: MatchStrength
    match_score: Decimal
    match_fields: List[str]
    status: AlertStatus = AlertStatus.NEW
    assigned_to: Optional[str] = None
    assigned_date: Optional[datetime] = None
    decision: Optional[str] = None
    decision_rationale: Optional[str] = None
    decided_by: Optional[str] = None
    decision_date: Optional[datetime] = None
    escalated_to: Optional[str] = None
    escalation_date: Optional[datetime] = None
    sla_due_date: datetime
    is_overdue: bool = False


class SanctionsCase(BaseModel):
    case_id: UUID = Field(default_factory=uuid4)
    case_reference: str
    case_type: str  # potential_match, blocked_transaction, license_review
    source_alert_ids: List[UUID]
    customer_id: Optional[str] = None
    transaction_ids: List[str] = Field(default_factory=list)
    case_status: str = "open"
    priority: str  # high, medium, low
    assigned_to: str
    assigned_date: datetime
    investigation_notes: List[Dict[str, Any]] = Field(default_factory=list)
    documents_collected: List[str] = Field(default_factory=list)
    ofac_license_required: bool = False
    license_reference: Optional[str] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None
    regulatory_filing_required: bool = False
    filing_reference: Optional[str] = None
    final_decision: Optional[str] = None
    decision_date: Optional[datetime] = None
    closed_by: Optional[str] = None
    closed_date: Optional[datetime] = None


class BlockedTransaction(BaseModel):
    blocked_id: UUID = Field(default_factory=uuid4)
    transaction_id: str
    transaction_type: str
    transaction_date: datetime
    amount: Decimal
    currency: str
    originator: str
    originator_account: str
    beneficiary: str
    beneficiary_account: str
    blocking_reason: str
    blocked_date: datetime
    list_source: SanctionsList
    matched_entry: str
    case_id: Optional[UUID] = None
    status: str = "blocked"
    release_authorized: bool = False
    release_authorization: Optional[str] = None
    release_date: Optional[datetime] = None
    rejected: bool = False
    rejection_date: Optional[datetime] = None
    regulatory_reported: bool = False
    report_date: Optional[datetime] = None


class SanctionsListUpdate(BaseModel):
    update_id: UUID = Field(default_factory=uuid4)
    list_source: SanctionsList
    update_date: date
    update_type: str  # additions, deletions, modifications
    entries_added: int
    entries_removed: int
    entries_modified: int
    file_reference: str
    processed_date: datetime
    processed_by: str
    rescreening_triggered: bool = False
    rescreening_completed: bool = False
    new_alerts_generated: int = 0


class SanctionsReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_date: date
    reporting_period: str
    total_screenings: int
    screenings_by_type: Dict[str, int]
    total_alerts: int
    alerts_by_strength: Dict[str, int]
    true_matches: int
    false_positives: int
    false_positive_rate: Decimal
    blocked_transactions: int
    blocked_amount: Decimal
    cases_opened: int
    cases_closed: int
    average_resolution_time: float
    escalations: int
    regulatory_filings: int
    list_updates_processed: int
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
