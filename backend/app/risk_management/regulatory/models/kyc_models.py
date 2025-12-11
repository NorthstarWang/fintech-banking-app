"""KYC Models - Data models for Know Your Customer compliance"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    TRUST = "trust"
    PARTNERSHIP = "partnership"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class RiskRating(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class DocumentType(str, Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    COMPANY_REGISTRATION = "company_registration"
    ARTICLES_OF_INCORPORATION = "articles_of_incorporation"
    FINANCIAL_STATEMENT = "financial_statement"


class CustomerProfile(BaseModel):
    profile_id: UUID = Field(default_factory=uuid4)
    customer_id: str
    customer_type: CustomerType
    full_name: str
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    country_of_residence: str
    address: str
    occupation: Optional[str] = None
    employer: Optional[str] = None
    source_of_funds: str
    source_of_wealth: Optional[str] = None
    expected_activity: str
    expected_monthly_volume: Decimal
    pep_status: bool = False
    pep_details: Optional[str] = None
    sanctions_status: bool = False
    adverse_media: bool = False
    risk_rating: RiskRating = RiskRating.MEDIUM
    risk_score: int = 50
    onboarding_date: date
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CorporateCustomer(BaseModel):
    corporate_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    legal_name: str
    trading_name: Optional[str] = None
    registration_number: str
    registration_country: str
    registration_date: date
    legal_form: str
    industry_sector: str
    business_description: str
    website: Optional[str] = None
    annual_revenue: Optional[Decimal] = None
    employee_count: Optional[int] = None
    beneficial_owners: List[Dict[str, Any]] = Field(default_factory=list)
    directors: List[Dict[str, Any]] = Field(default_factory=list)
    authorized_signatories: List[Dict[str, Any]] = Field(default_factory=list)
    parent_company: Optional[str] = None
    subsidiaries: List[str] = Field(default_factory=list)
    complex_structure: bool = False
    structure_diagram: Optional[str] = None


class IdentityVerification(BaseModel):
    verification_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    verification_type: str  # identity, address, document
    document_type: DocumentType
    document_number: str
    issuing_country: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    verification_method: str  # manual, automated, third_party
    verification_provider: Optional[str] = None
    verification_reference: Optional[str] = None
    status: VerificationStatus = VerificationStatus.PENDING
    verification_date: Optional[datetime] = None
    verified_by: Optional[str] = None
    failure_reason: Optional[str] = None
    document_location: str
    confidence_score: Optional[Decimal] = None


class EnhancedDueDiligence(BaseModel):
    edd_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    trigger_reason: str
    edd_date: date
    conducted_by: str
    source_of_wealth_verified: bool = False
    source_of_funds_verified: bool = False
    business_relationship_purpose: str
    expected_transactions: str
    geographical_exposure: List[str]
    pep_screening_result: Optional[str] = None
    sanctions_screening_result: Optional[str] = None
    adverse_media_result: Optional[str] = None
    site_visit_conducted: bool = False
    site_visit_date: Optional[date] = None
    management_approval: bool = False
    approval_date: Optional[date] = None
    approved_by: Optional[str] = None
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    next_review_date: date
    status: str = "pending"


class PeriodicReview(BaseModel):
    review_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    review_type: str  # annual, event_triggered, risk_based
    review_date: date
    reviewer: str
    previous_risk_rating: RiskRating
    new_risk_rating: RiskRating
    risk_score_change: int
    changes_identified: List[str]
    documents_updated: List[str]
    screening_results: Dict[str, str]
    transaction_review: Dict[str, Any]
    sar_filed: bool = False
    recommendations: List[str]
    action_items: List[Dict[str, Any]]
    next_review_date: date
    status: str = "completed"
    approved_by: Optional[str] = None


class BeneficialOwner(BaseModel):
    owner_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID  # Corporate profile
    individual_profile_id: Optional[UUID] = None
    full_name: str
    date_of_birth: date
    nationality: str
    country_of_residence: str
    ownership_percentage: Decimal
    ownership_type: str  # direct, indirect
    control_type: Optional[str] = None  # voting_rights, board_control, etc.
    verification_status: VerificationStatus = VerificationStatus.PENDING
    pep_status: bool = False
    sanctions_status: bool = False
    verified_date: Optional[date] = None
    is_active: bool = True


class KYCReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    report_date: date
    reporting_period: str
    total_customers: int
    new_customers: int
    high_risk_customers: int
    medium_risk_customers: int
    low_risk_customers: int
    pep_customers: int
    verifications_completed: int
    verifications_failed: int
    edd_conducted: int
    periodic_reviews_completed: int
    periodic_reviews_overdue: int
    sars_filed: int
    accounts_closed: int
    average_onboarding_time: float
    compliance_score: float
    generated_by: str
