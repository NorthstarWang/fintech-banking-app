"""
KYC (Know Your Customer) Models

Defines data structures for customer due diligence and KYC processes.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class KYCStatus(str, Enum):
    """KYC verification status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_DOCUMENTS = "pending_documents"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class KYCLevel(str, Enum):
    """Level of KYC verification"""
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    SIMPLIFIED = "simplified"


class DocumentType(str, Enum):
    """Types of identity documents"""
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    RESIDENCE_PERMIT = "residence_permit"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    COMPANY_REGISTRATION = "company_registration"
    ARTICLES_OF_INCORPORATION = "articles_of_incorporation"
    SHAREHOLDER_REGISTER = "shareholder_register"
    FINANCIAL_STATEMENT = "financial_statement"
    PROOF_OF_ADDRESS = "proof_of_address"
    SOURCE_OF_FUNDS = "source_of_funds"
    SOURCE_OF_WEALTH = "source_of_wealth"


class VerificationMethod(str, Enum):
    """Methods of verification"""
    DOCUMENT_UPLOAD = "document_upload"
    BIOMETRIC = "biometric"
    VIDEO_CALL = "video_call"
    IN_PERSON = "in_person"
    DATABASE_CHECK = "database_check"
    THIRD_PARTY = "third_party"


class IdentityDocument(BaseModel):
    """Identity document record"""
    document_id: UUID = Field(default_factory=uuid4)
    document_type: DocumentType
    document_number: Optional[str] = None

    # Document details
    issuing_country: str
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None

    # File information
    file_path: str
    file_name: str
    file_size: int
    mime_type: str

    # Verification
    verification_status: str = "pending"  # pending, verified, rejected
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # OCR extracted data
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    ocr_confidence: float = 0.0

    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class AddressVerification(BaseModel):
    """Address verification record"""
    verification_id: UUID = Field(default_factory=uuid4)

    # Address
    address_type: str  # residential, business, mailing
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str

    # Verification
    verification_method: VerificationMethod
    verification_status: str = "pending"
    verification_date: Optional[datetime] = None
    verified_by: Optional[str] = None

    # Supporting document
    document_id: Optional[UUID] = None
    document_type: Optional[DocumentType] = None

    # Validity
    valid_from: datetime
    valid_until: Optional[datetime] = None

    # Third-party verification
    third_party_provider: Optional[str] = None
    third_party_reference: Optional[str] = None
    third_party_result: Optional[Dict[str, Any]] = None


class BiometricVerification(BaseModel):
    """Biometric verification record"""
    verification_id: UUID = Field(default_factory=uuid4)

    # Biometric type
    biometric_type: str  # facial, fingerprint, voice
    capture_method: str

    # Verification result
    verification_status: str = "pending"
    match_score: float = 0.0
    liveness_score: float = 0.0
    quality_score: float = 0.0

    # Reference
    reference_document_id: Optional[UUID] = None

    # Provider
    provider: str
    provider_reference: str
    provider_result: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None


class SourceOfFunds(BaseModel):
    """Source of funds declaration"""
    source_id: UUID = Field(default_factory=uuid4)

    # Source type
    source_type: str  # employment, business, inheritance, investment, savings, gift, loan
    description: str

    # Amount
    amount: Optional[float] = None
    currency: str = "USD"
    percentage_of_total: Optional[float] = None

    # Supporting documents
    document_ids: List[UUID] = Field(default_factory=list)

    # Verification
    verification_status: str = "pending"
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None


class SourceOfWealth(BaseModel):
    """Source of wealth declaration"""
    source_id: UUID = Field(default_factory=uuid4)

    # Source type
    source_type: str  # business_ownership, inheritance, investments, real_estate, employment
    description: str

    # Estimated value
    estimated_value: Optional[float] = None
    currency: str = "USD"

    # Period accumulated
    accumulated_since: Optional[date] = None

    # Supporting documents
    document_ids: List[UUID] = Field(default_factory=list)

    # Verification
    verification_status: str = "pending"
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


class BeneficialOwner(BaseModel):
    """Beneficial owner information (for entities)"""
    owner_id: UUID = Field(default_factory=uuid4)

    # Personal information
    first_name: str
    last_name: str
    date_of_birth: date
    nationality: str
    tax_residence: str

    # Ownership
    ownership_percentage: float
    ownership_type: str  # direct, indirect
    control_type: Optional[str] = None  # voting, management

    # Contact
    address: Optional[str] = None
    country_of_residence: str

    # Identification
    id_type: DocumentType
    id_number: str
    id_issuing_country: str
    id_expiry_date: Optional[date] = None

    # PEP status
    is_pep: bool = False
    pep_details: Optional[str] = None

    # Verification
    verification_status: str = "pending"
    documents: List[UUID] = Field(default_factory=list)


class KYCCheck(BaseModel):
    """Individual KYC check"""
    check_id: UUID = Field(default_factory=uuid4)
    check_type: str  # identity, address, sanctions, pep, adverse_media
    check_name: str

    # Status
    status: str = "pending"
    result: Optional[str] = None  # pass, fail, review_required
    risk_level: Optional[str] = None

    # Provider
    provider: Optional[str] = None
    provider_reference: Optional[str] = None
    provider_result: Dict[str, Any] = Field(default_factory=dict)

    # Findings
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[str] = Field(default_factory=list)

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Review
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class KYCProfile(BaseModel):
    """Complete KYC profile for a customer"""
    profile_id: UUID = Field(default_factory=uuid4)
    customer_id: str
    customer_type: str  # individual, corporate

    # Status
    kyc_status: KYCStatus = KYCStatus.NOT_STARTED
    kyc_level: KYCLevel = KYCLevel.STANDARD

    # Personal/Entity information
    full_name: str
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    tax_id: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None

    # For corporate
    company_name: Optional[str] = None
    registration_number: Optional[str] = None
    incorporation_country: Optional[str] = None
    incorporation_date: Optional[date] = None
    business_type: Optional[str] = None

    # Documents
    identity_documents: List[IdentityDocument] = Field(default_factory=list)

    # Address verifications
    address_verifications: List[AddressVerification] = Field(default_factory=list)

    # Biometrics
    biometric_verifications: List[BiometricVerification] = Field(default_factory=list)

    # Source of funds/wealth
    sources_of_funds: List[SourceOfFunds] = Field(default_factory=list)
    sources_of_wealth: List[SourceOfWealth] = Field(default_factory=list)

    # Beneficial owners (for corporate)
    beneficial_owners: List[BeneficialOwner] = Field(default_factory=list)

    # KYC checks performed
    checks: List[KYCCheck] = Field(default_factory=list)

    # Risk assessment
    risk_score: float = 0.0
    risk_level: str = "medium"
    risk_factors: List[str] = Field(default_factory=list)

    # PEP status
    is_pep: bool = False
    pep_level: Optional[str] = None
    pep_details: Optional[str] = None

    # Sanctions
    sanctions_hit: bool = False
    sanctions_details: Optional[str] = None

    # Adverse media
    adverse_media_hit: bool = False
    adverse_media_details: Optional[str] = None

    # EDD
    requires_edd: bool = False
    edd_reason: Optional[str] = None
    edd_completed: bool = False
    edd_completed_at: Optional[datetime] = None

    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Review schedule
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[date] = None
    review_frequency_months: int = 12

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class EDDRequest(BaseModel):
    """Enhanced Due Diligence request"""
    edd_id: UUID = Field(default_factory=uuid4)
    customer_id: str
    kyc_profile_id: UUID

    # Reason for EDD
    trigger_reason: str
    trigger_type: str  # pep, high_risk_country, high_value, sanctions_hit, adverse_media
    triggered_by: str
    triggered_at: datetime = Field(default_factory=datetime.utcnow)

    # Required information
    required_documents: List[DocumentType] = Field(default_factory=list)
    required_checks: List[str] = Field(default_factory=list)
    additional_questions: List[str] = Field(default_factory=list)

    # Status
    status: str = "open"  # open, in_progress, completed, cancelled
    assigned_to: Optional[str] = None

    # Findings
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Optional[str] = None
    recommendation: Optional[str] = None

    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Timestamps
    due_date: datetime
    completed_at: Optional[datetime] = None


class OnboardingWorkflow(BaseModel):
    """Customer onboarding workflow"""
    workflow_id: UUID = Field(default_factory=uuid4)
    customer_id: str

    # Workflow status
    status: str = "initiated"
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)

    # Customer type
    customer_type: str
    product_type: str

    # KYC profile
    kyc_profile_id: Optional[UUID] = None

    # Required checks based on product/customer type
    required_kyc_level: KYCLevel
    required_documents: List[DocumentType] = Field(default_factory=list)
    required_checks: List[str] = Field(default_factory=list)

    # Progress
    documents_collected: int = 0
    documents_required: int = 0
    checks_completed: int = 0
    checks_required: int = 0

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: datetime

    # Assigned reviewer
    assigned_to: Optional[str] = None


class KYCStatistics(BaseModel):
    """KYC statistics for reporting"""
    total_profiles: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_kyc_level: Dict[str, int] = Field(default_factory=dict)
    by_risk_level: Dict[str, int] = Field(default_factory=dict)
    onboarding_in_progress: int = 0
    pending_review: int = 0
    expired_profiles: int = 0
    requiring_edd: int = 0
    pep_count: int = 0
    high_risk_count: int = 0
    average_onboarding_days: float = 0.0
    document_rejection_rate: float = 0.0
