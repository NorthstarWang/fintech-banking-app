"""
KYC Routes

API endpoints for KYC management.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.kyc_models import (
    KYCProfile, KYCStatus, KYCLevel, IdentityDocument, AddressVerification,
    BiometricVerification, SourceOfFunds, SourceOfWealth, BeneficialOwner,
    KYCCheck, EDDRequest, OnboardingWorkflow, KYCStatistics
)
from ..services.kyc_service import kyc_service

router = APIRouter(prefix="/aml/kyc", tags=["KYC"])


@router.post("/profiles", response_model=KYCProfile)
async def create_profile(customer_id: str, customer_type: str, full_name: str):
    """Create a new KYC profile"""
    return await kyc_service.create_profile(customer_id, customer_type, full_name)


@router.get("/profiles/{profile_id}", response_model=KYCProfile)
async def get_profile(profile_id: UUID):
    """Get KYC profile by ID"""
    profile = await kyc_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/profiles/customer/{customer_id}", response_model=KYCProfile)
async def get_profile_by_customer(customer_id: str):
    """Get KYC profile by customer ID"""
    profile = await kyc_service.get_profile_by_customer(customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profiles/{profile_id}/status")
async def update_profile_status(profile_id: UUID, status: KYCStatus, updated_by: str = "system"):
    """Update KYC profile status"""
    profile = await kyc_service.update_profile_status(profile_id, status, updated_by)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/profiles/{profile_id}/documents")
async def add_identity_document(profile_id: UUID, document: IdentityDocument):
    """Add identity document to profile"""
    profile = await kyc_service.add_identity_document(profile_id, document)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}


@router.put("/profiles/{profile_id}/documents/{document_id}/verify")
async def verify_document(
    profile_id: UUID, document_id: UUID, verified_by: str, is_verified: bool,
    rejection_reason: Optional[str] = None
):
    """Verify an identity document"""
    doc = await kyc_service.verify_document(profile_id, document_id, verified_by, is_verified, rejection_reason)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/profiles/{profile_id}/addresses")
async def add_address_verification(profile_id: UUID, address: AddressVerification):
    """Add address verification to profile"""
    profile = await kyc_service.add_address_verification(profile_id, address)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}


@router.post("/profiles/{profile_id}/biometrics")
async def add_biometric_verification(profile_id: UUID, biometric: BiometricVerification):
    """Add biometric verification to profile"""
    profile = await kyc_service.add_biometric_verification(profile_id, biometric)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}


@router.post("/profiles/{profile_id}/source-of-funds")
async def add_source_of_funds(profile_id: UUID, source: SourceOfFunds):
    """Add source of funds declaration"""
    profile = await kyc_service.add_source_of_funds(profile_id, source)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}


@router.post("/profiles/{profile_id}/source-of-wealth")
async def add_source_of_wealth(profile_id: UUID, source: SourceOfWealth):
    """Add source of wealth declaration"""
    profile = await kyc_service.add_source_of_wealth(profile_id, source)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}


@router.post("/profiles/{profile_id}/beneficial-owners")
async def add_beneficial_owner(profile_id: UUID, owner: BeneficialOwner):
    """Add beneficial owner"""
    profile = await kyc_service.add_beneficial_owner(profile_id, owner)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success"}


@router.post("/profiles/{profile_id}/checks")
async def run_kyc_check(
    profile_id: UUID, check_type: str, check_name: str, provider: Optional[str] = None
):
    """Run a KYC check"""
    check = await kyc_service.run_kyc_check(profile_id, check_type, check_name, provider)
    if not check:
        raise HTTPException(status_code=404, detail="Profile not found")
    return check


@router.post("/profiles/{profile_id}/calculate-risk")
async def calculate_risk_score(profile_id: UUID):
    """Calculate customer risk score"""
    score = await kyc_service.calculate_risk_score(profile_id)
    if score is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"risk_score": score}


@router.post("/profiles/{profile_id}/edd")
async def request_edd(
    profile_id: UUID, trigger_reason: str, trigger_type: str, triggered_by: str = "system"
):
    """Request Enhanced Due Diligence"""
    edd = await kyc_service.request_edd(profile_id, trigger_reason, trigger_type, triggered_by)
    if not edd:
        raise HTTPException(status_code=404, detail="Profile not found")
    return edd


@router.post("/onboarding")
async def start_onboarding(customer_id: str, customer_type: str, product_type: str):
    """Start customer onboarding workflow"""
    return await kyc_service.start_onboarding(customer_id, customer_type, product_type)


@router.get("/statistics", response_model=KYCStatistics)
async def get_statistics():
    """Get KYC statistics"""
    return await kyc_service.get_statistics()
