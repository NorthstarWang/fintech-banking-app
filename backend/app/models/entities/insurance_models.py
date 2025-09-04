from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Insurance-specific enums
class InsuranceType(str, Enum):
    HEALTH = "health"
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"
    DISABILITY = "disability"
    DENTAL = "dental"
    VISION = "vision"
    PET = "pet"
    TRAVEL = "travel"
    CRYPTO = "crypto"  # For digital asset insurance
    CYBER = "cyber"    # Cyber security insurance

class PolicyStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    LAPSED = "lapsed"

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    APPEALED = "appealed"
    CLOSED = "closed"

class PremiumFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"

class CoverageType(str, Enum):
    LIABILITY = "liability"
    COLLISION = "collision"
    COMPREHENSIVE = "comprehensive"
    MEDICAL = "medical"
    PROPERTY = "property"
    TERM_LIFE = "term_life"
    WHOLE_LIFE = "whole_life"
    SHORT_TERM_DISABILITY = "short_term_disability"
    LONG_TERM_DISABILITY = "long_term_disability"

# Request/Response Models
class InsurancePolicyCreate(BaseModel):
    insurance_type: InsuranceType
    provider_name: str
    policy_number: str
    coverage_amount: float
    deductible: float
    premium_amount: float
    premium_frequency: PremiumFrequency
    start_date: date
    end_date: date
    beneficiaries: Optional[List[Dict[str, str]]] = None
    coverage_details: Optional[Dict[str, Any]] = None

class InsurancePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    insurance_type: InsuranceType
    provider_name: str
    policy_number: str
    status: PolicyStatus
    coverage_amount: float
    deductible: float
    out_of_pocket_max: Optional[float] = None
    premium_amount: float
    premium_frequency: PremiumFrequency
    next_premium_date: date
    start_date: date
    end_date: date
    renewal_date: Optional[date] = None
    beneficiaries: Optional[List[Dict[str, str]]] = None
    coverage_details: Dict[str, Any]
    documents: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime

class InsuranceClaimCreate(BaseModel):
    policy_id: int
    claim_type: str
    incident_date: date
    amount_claimed: float
    description: str
    supporting_documents: Optional[List[str]] = None
    provider_details: Optional[Dict[str, str]] = None

class InsuranceClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    policy_id: int
    claim_number: str
    claim_type: str
    status: ClaimStatus
    incident_date: date
    filed_date: datetime
    amount_claimed: float
    amount_approved: Optional[float] = None
    amount_paid: Optional[float] = None
    deductible_applied: Optional[float] = None
    description: str
    adjuster_name: Optional[str] = None
    adjuster_notes: Optional[str] = None
    denial_reason: Optional[str] = None
    documents: List[Dict[str, str]]
    status_history: List[Dict[str, Any]]
    payment_date: Optional[datetime] = None
    appeal_deadline: Optional[date] = None
    created_at: datetime
    updated_at: datetime

class InsuranceProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    insurance_types: List[InsuranceType]
    rating: float
    customer_service_phone: str
    customer_service_email: Optional[str] = None
    website: str
    claim_phone: str
    network_size: Optional[int] = None  # For health insurance
    financial_strength_rating: Optional[str] = None
    complaint_ratio: Optional[float] = None

class InsuranceQuoteRequest(BaseModel):
    insurance_type: InsuranceType
    coverage_amount: float
    deductible: float
    personal_info: Dict[str, Any]  # Age, location, etc.
    coverage_options: Optional[List[str]] = None

class InsuranceQuoteResponse(BaseModel):
    provider_name: str
    monthly_premium: float
    annual_premium: float
    coverage_amount: float
    deductible: float
    coverage_details: Dict[str, Any]
    discounts_applied: List[str]
    quote_id: str
    valid_until: datetime

class InsuranceSummaryResponse(BaseModel):
    total_policies: int
    active_policies: int
    total_monthly_premiums: float
    total_annual_premiums: float
    total_coverage_amount: float
    policies_by_type: Dict[str, int]
    upcoming_renewals: List[Dict[str, Any]]
    recent_claims: List[Dict[str, Any]]
    coverage_gaps: List[str]

class HealthInsuranceDetails(BaseModel):
    in_network_deductible: float
    out_network_deductible: float
    in_network_oop_max: float
    out_network_oop_max: float
    copay_primary: float
    copay_specialist: float
    copay_emergency: float
    prescription_coverage: Dict[str, Any]
    preventive_care_covered: bool
    hsafsa_eligible: bool

class AutoInsuranceDetails(BaseModel):
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    vin: str
    liability_coverage: float
    collision_coverage: Optional[float] = None
    comprehensive_coverage: Optional[float] = None
    uninsured_motorist: Optional[float] = None
    rental_reimbursement: Optional[float] = None
    roadside_assistance: bool

class ClaimTimelineEvent(BaseModel):
    event_date: datetime
    event_type: str
    description: str
    performed_by: Optional[str] = None
    notes: Optional[str] = None