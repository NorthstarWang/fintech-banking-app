"""KYC Compliance API Routes"""

from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.kyc_models import CustomerType, RiskRating
from ..services.kyc_service import kyc_service

router = APIRouter(prefix="/kyc", tags=["KYC Compliance"])


class CustomerOnboardingRequest(BaseModel):
    customer_id: str
    customer_name: str
    customer_type: CustomerType
    country_of_residence: str
    nationality: str
    date_of_birth: Optional[date] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    occupation: Optional[str] = None
    source_of_funds: str
    expected_activity: str


class VerificationRequest(BaseModel):
    customer_id: str
    verification_type: str
    document_type: str
    document_number: str
    issuing_country: str
    expiry_date: Optional[date] = None
    verified_by: str


class EDDRequest(BaseModel):
    customer_id: str
    trigger_reason: str
    additional_documents: List[str]
    source_of_wealth: str
    business_rationale: str
    conducted_by: str


class PeriodicReviewRequest(BaseModel):
    customer_id: str
    review_type: str
    reviewer: str


class BeneficialOwnerRequest(BaseModel):
    customer_id: str
    owner_name: str
    ownership_percentage: Decimal
    nationality: str
    date_of_birth: date
    relationship: str


class PEPScreeningRequest(BaseModel):
    customer_id: str
    name_screened: str
    screening_provider: str


class AdverseMediaRequest(BaseModel):
    customer_id: str
    search_terms: List[str]
    screened_by: str


@router.post("/onboard", response_model=dict)
async def onboard_customer(request: CustomerOnboardingRequest):
    """Onboard a new customer with KYC profile"""
    profile = await kyc_service.onboard_customer(
        customer_id=request.customer_id, customer_name=request.customer_name,
        customer_type=request.customer_type, country_of_residence=request.country_of_residence,
        nationality=request.nationality, date_of_birth=request.date_of_birth,
        tax_id=request.tax_id, industry=request.industry, occupation=request.occupation,
        source_of_funds=request.source_of_funds, expected_activity=request.expected_activity
    )
    return {
        "profile_id": str(profile.profile_id),
        "risk_rating": profile.risk_rating,
        "risk_score": profile.risk_score,
        "next_review_date": str(profile.next_review_date)
    }


@router.get("/profile/{customer_id}", response_model=dict)
async def get_customer_profile(customer_id: str):
    """Get KYC profile for a customer"""
    profile = await kyc_service.repository.find_profile_by_customer_id(customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    return {
        "profile_id": str(profile.profile_id),
        "customer_name": profile.customer_name,
        "customer_type": profile.customer_type.value,
        "risk_rating": profile.risk_rating,
        "kyc_status": profile.kyc_status
    }


@router.get("/profiles", response_model=List[dict])
async def list_profiles(
    risk_rating: Optional[str] = None,
    due_for_review: bool = False
):
    """List customer profiles"""
    if risk_rating:
        profiles = await kyc_service.repository.find_profiles_by_risk_rating(risk_rating)
    elif due_for_review:
        profiles = await kyc_service.repository.find_profiles_due_for_review(date.today())
    else:
        profiles = await kyc_service.repository.find_all_profiles()
    return [{"profile_id": str(p.profile_id), "customer_name": p.customer_name, "risk_rating": p.risk_rating} for p in profiles]


@router.post("/verify", response_model=dict)
async def verify_customer(request: VerificationRequest):
    """Perform customer verification"""
    verification = await kyc_service.perform_verification(
        customer_id=request.customer_id, verification_type=request.verification_type,
        document_type=request.document_type, document_number=request.document_number,
        issuing_country=request.issuing_country, expiry_date=request.expiry_date,
        verified_by=request.verified_by
    )
    return {
        "verification_id": str(verification.verification_id),
        "verification_status": verification.verification_status,
        "confidence_score": verification.confidence_score
    }


@router.get("/verifications/{customer_id}", response_model=List[dict])
async def get_customer_verifications(customer_id: str):
    """Get all verifications for a customer"""
    verifications = await kyc_service.repository.find_verifications_by_customer(customer_id)
    return [{"verification_id": str(v.verification_id), "verification_type": v.verification_type, "verification_status": v.verification_status} for v in verifications]


@router.post("/edd", response_model=dict)
async def conduct_edd(request: EDDRequest):
    """Conduct Enhanced Due Diligence"""
    edd = await kyc_service.conduct_edd(
        customer_id=request.customer_id, trigger_reason=request.trigger_reason,
        additional_documents=request.additional_documents, source_of_wealth=request.source_of_wealth,
        business_rationale=request.business_rationale, conducted_by=request.conducted_by
    )
    return {
        "edd_id": str(edd.edd_id),
        "edd_level": edd.edd_level,
        "approval_status": edd.approval_status
    }


@router.post("/edd/{edd_id}/approve", response_model=dict)
async def approve_edd(edd_id: UUID, approved_by: str = Query(...), recommendation: str = Query(...)):
    """Approve EDD findings"""
    edd = await kyc_service.approve_edd(edd_id, approved_by, recommendation)
    if not edd:
        raise HTTPException(status_code=404, detail="EDD not found")
    return {"edd_id": str(edd.edd_id), "approval_status": edd.approval_status}


@router.post("/periodic-review", response_model=dict)
async def perform_periodic_review(request: PeriodicReviewRequest):
    """Perform periodic KYC review"""
    review = await kyc_service.perform_periodic_review(
        customer_id=request.customer_id, review_type=request.review_type, reviewer=request.reviewer
    )
    return {
        "review_id": str(review.review_id),
        "review_status": review.review_status,
        "next_review_date": str(review.next_review_date)
    }


@router.get("/reviews/overdue", response_model=List[dict])
async def list_overdue_reviews():
    """List overdue periodic reviews"""
    reviews = await kyc_service.repository.find_overdue_reviews()
    return [{"review_id": str(r.review_id), "customer_id": r.customer_id, "due_date": str(r.due_date)} for r in reviews]


@router.post("/beneficial-owners", response_model=dict)
async def register_beneficial_owner(request: BeneficialOwnerRequest):
    """Register a beneficial owner"""
    owner = await kyc_service.register_beneficial_owner(
        customer_id=request.customer_id, owner_name=request.owner_name,
        ownership_percentage=request.ownership_percentage, nationality=request.nationality,
        date_of_birth=request.date_of_birth, relationship=request.relationship
    )
    return {"owner_id": str(owner.owner_id), "owner_name": owner.owner_name}


@router.get("/beneficial-owners/{customer_id}", response_model=List[dict])
async def get_beneficial_owners(customer_id: str):
    """Get beneficial owners for a customer"""
    owners = await kyc_service.repository.find_beneficial_owners_by_customer(customer_id)
    return [{"owner_id": str(o.owner_id), "owner_name": o.owner_name, "ownership_percentage": float(o.ownership_percentage)} for o in owners]


@router.post("/pep-screening", response_model=dict)
async def screen_for_pep(request: PEPScreeningRequest):
    """Screen customer for PEP status"""
    screening = await kyc_service.screen_for_pep(
        customer_id=request.customer_id, name_screened=request.name_screened,
        screening_provider=request.screening_provider
    )
    return {
        "screening_id": str(screening.screening_id),
        "pep_match": screening.pep_match,
        "pep_category": screening.pep_category,
        "rca_match": screening.rca_match
    }


@router.get("/pep-screenings/matches", response_model=List[dict])
async def list_pep_matches():
    """List all PEP matches"""
    matches = await kyc_service.repository.find_pep_matches()
    return [{"screening_id": str(s.screening_id), "customer_id": s.customer_id, "pep_category": s.pep_category} for s in matches]


@router.post("/adverse-media", response_model=dict)
async def check_adverse_media(request: AdverseMediaRequest):
    """Check for adverse media"""
    media = await kyc_service.check_adverse_media(
        customer_id=request.customer_id, search_terms=request.search_terms, screened_by=request.screened_by
    )
    return {
        "media_id": str(media.media_id),
        "adverse_findings": media.adverse_findings,
        "risk_indicator": media.risk_indicator
    }


@router.post("/reports/generate", response_model=dict)
async def generate_kyc_report(reporting_period: str = Query(...), generated_by: str = Query(...)):
    """Generate KYC compliance report"""
    report = await kyc_service.generate_report(reporting_period=reporting_period, generated_by=generated_by)
    return {"report_id": str(report.report_id), "report_date": str(report.report_date)}


@router.get("/statistics", response_model=dict)
async def get_kyc_statistics():
    """Get KYC compliance statistics"""
    return await kyc_service.get_statistics()
