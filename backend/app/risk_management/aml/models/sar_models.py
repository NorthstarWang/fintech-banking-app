"""
SAR (Suspicious Activity Report) Models

Defines data structures for SAR filing and management.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SARStatus(str, Enum):
    """SAR filing status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    AMENDED = "amended"


class SARType(str, Enum):
    """Type of SAR"""
    INITIAL = "initial"
    CONTINUING = "continuing"
    CORRECTED = "corrected"
    JOINT = "joint"


class SuspiciousActivityType(str, Enum):
    """Types of suspicious activity"""
    MONEY_LAUNDERING = "money_laundering"
    STRUCTURING = "structuring"
    TERRORIST_FINANCING = "terrorist_financing"
    FRAUD = "fraud"
    IDENTITY_THEFT = "identity_theft"
    CHECK_FRAUD = "check_fraud"
    LOAN_FRAUD = "loan_fraud"
    CREDIT_CARD_FRAUD = "credit_card_fraud"
    WIRE_TRANSFER_FRAUD = "wire_transfer_fraud"
    MORTGAGE_FRAUD = "mortgage_fraud"
    INSIDER_ABUSE = "insider_abuse"
    BRIBERY = "bribery"
    EMBEZZLEMENT = "embezzlement"
    TAX_EVASION = "tax_evasion"
    SANCTIONS_VIOLATION = "sanctions_violation"
    OTHER = "other"


class FilingInstitution(BaseModel):
    """Institution filing the SAR"""
    institution_name: str
    institution_type: str
    ein: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "US"
    regulator: str
    regulatory_id: str


class SubjectInfo(BaseModel):
    """Subject of the SAR"""
    subject_id: UUID = Field(default_factory=uuid4)
    subject_type: str  # individual, entity
    is_internal: bool = False

    # Individual info
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    suffix: Optional[str] = None
    date_of_birth: Optional[date] = None
    ssn_tin: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    drivers_license: Optional[str] = None
    drivers_license_state: Optional[str] = None

    # Entity info
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    ein: Optional[str] = None
    naics_code: Optional[str] = None

    # Contact info
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone_numbers: List[str] = Field(default_factory=list)
    email_addresses: List[str] = Field(default_factory=list)

    # Relationship
    relationship_to_institution: Optional[str] = None
    account_numbers: List[str] = Field(default_factory=list)

    # Role
    role_in_activity: str = "subject"  # subject, beneficiary, conductor


class SuspiciousActivity(BaseModel):
    """Details of suspicious activity"""
    activity_id: UUID = Field(default_factory=uuid4)
    activity_type: SuspiciousActivityType
    activity_description: str

    # Date range
    date_first_detected: datetime
    date_activity_started: Optional[datetime] = None
    date_activity_ended: Optional[datetime] = None

    # Amount
    total_amount: float = 0.0
    currency: str = "USD"

    # Instruments
    instruments_involved: List[str] = Field(default_factory=list)  # cash, wire, check, etc.

    # Products/Services
    products_involved: List[str] = Field(default_factory=list)

    # Geographic
    countries_involved: List[str] = Field(default_factory=list)


class TransactionDetail(BaseModel):
    """Transaction details for SAR"""
    transaction_id: str
    transaction_date: datetime
    transaction_type: str
    amount: float
    currency: str = "USD"
    direction: str  # in, out
    counterparty_name: Optional[str] = None
    counterparty_account: Optional[str] = None
    counterparty_institution: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class Narrative(BaseModel):
    """SAR narrative section"""
    narrative_id: UUID = Field(default_factory=uuid4)
    section: str  # who, what, when, where, why, how
    content: str
    version: int = 1
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None


class SARDocument(BaseModel):
    """Document attached to SAR"""
    document_id: UUID = Field(default_factory=uuid4)
    document_name: str
    document_type: str
    file_path: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class SARApproval(BaseModel):
    """Approval record for SAR"""
    approval_id: UUID = Field(default_factory=uuid4)
    approver_id: str
    approver_name: str
    approver_role: str
    decision: str  # approved, rejected, returned
    comments: Optional[str] = None
    approved_at: datetime = Field(default_factory=datetime.utcnow)


class SARSubmission(BaseModel):
    """SAR submission record"""
    submission_id: UUID = Field(default_factory=uuid4)
    submission_date: datetime
    submission_method: str  # efiling, batch
    batch_id: Optional[str] = None

    # Filing reference
    bsa_id: Optional[str] = None  # BSA tracking number
    acknowledgment_number: Optional[str] = None

    # Response
    response_received: bool = False
    response_date: Optional[datetime] = None
    response_status: Optional[str] = None
    response_errors: List[str] = Field(default_factory=list)


class SAR(BaseModel):
    """Main SAR entity"""
    sar_id: UUID = Field(default_factory=uuid4)
    sar_number: str

    # SAR type and status
    sar_type: SARType = SARType.INITIAL
    status: SARStatus = SARStatus.DRAFT

    # Prior SAR reference
    prior_sar_number: Optional[str] = None
    prior_bsa_id: Optional[str] = None

    # Filing institution
    filing_institution: FilingInstitution

    # Subjects
    subjects: List[SubjectInfo] = Field(default_factory=list)
    primary_subject_index: int = 0

    # Suspicious activity
    activities: List[SuspiciousActivity] = Field(default_factory=list)
    primary_activity_type: SuspiciousActivityType

    # Financial summary
    total_suspicious_amount: float = 0.0
    cumulative_amount: float = 0.0

    # Transactions
    transactions: List[TransactionDetail] = Field(default_factory=list)
    transaction_count: int = 0

    # Narrative
    narratives: List[Narrative] = Field(default_factory=list)
    full_narrative: Optional[str] = None

    # Law enforcement contact
    law_enforcement_contacted: bool = False
    law_enforcement_agency: Optional[str] = None
    law_enforcement_contact_date: Optional[datetime] = None

    # Documents
    documents: List[SARDocument] = Field(default_factory=list)

    # Related records
    case_ids: List[UUID] = Field(default_factory=list)
    alert_ids: List[UUID] = Field(default_factory=list)

    # Approval workflow
    approvals: List[SARApproval] = Field(default_factory=list)
    requires_approval_from: List[str] = Field(default_factory=list)

    # Submission
    submissions: List[SARSubmission] = Field(default_factory=list)
    last_submission: Optional[SARSubmission] = None

    # Filing deadline
    filing_deadline: datetime
    extension_granted: bool = False
    extension_reason: Optional[str] = None
    new_deadline: Optional[datetime] = None

    # Preparer info
    prepared_by: str
    prepared_at: datetime = Field(default_factory=datetime.utcnow)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SARSummary(BaseModel):
    """Summary view of a SAR for listings"""
    sar_id: UUID
    sar_number: str
    sar_type: SARType
    status: SARStatus
    primary_subject_name: str
    primary_activity_type: SuspiciousActivityType
    total_amount: float
    filing_deadline: datetime
    prepared_by: str
    created_at: datetime
    submitted_at: Optional[datetime] = None


class SARStatistics(BaseModel):
    """SAR statistics for reporting"""
    total_sars: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_activity_type: Dict[str, int] = Field(default_factory=dict)
    by_sar_type: Dict[str, int] = Field(default_factory=dict)
    filed_this_month: int = 0
    filed_this_quarter: int = 0
    filed_this_year: int = 0
    pending_filing: int = 0
    overdue: int = 0
    average_preparation_days: float = 0.0
    rejection_rate: float = 0.0


class SARCreateRequest(BaseModel):
    """Request to create a SAR"""
    sar_type: SARType = SARType.INITIAL
    prior_sar_number: Optional[str] = None
    case_ids: List[UUID] = Field(default_factory=list)
    alert_ids: List[UUID] = Field(default_factory=list)
    primary_activity_type: SuspiciousActivityType


class SARUpdateRequest(BaseModel):
    """Request to update a SAR"""
    status: Optional[SARStatus] = None
    subjects: Optional[List[SubjectInfo]] = None
    activities: Optional[List[SuspiciousActivity]] = None
    full_narrative: Optional[str] = None
    law_enforcement_contacted: Optional[bool] = None
    law_enforcement_agency: Optional[str] = None


class SARSearchCriteria(BaseModel):
    """Search criteria for SARs"""
    statuses: Optional[List[SARStatus]] = None
    sar_types: Optional[List[SARType]] = None
    activity_types: Optional[List[SuspiciousActivityType]] = None
    subject_names: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    prepared_by: Optional[List[str]] = None
    overdue_only: bool = False
    page: int = 1
    page_size: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"
