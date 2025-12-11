"""
Risk Scoring Routes

API endpoints for customer risk scoring.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.customer_risk_models import (
    CustomerRiskProfile, CustomerRiskAssessment, CustomerRiskLevel,
    CustomerType, GeographicRisk, RiskOverrideRequest
)
from ..services.risk_scoring_service import risk_scoring_service

router = APIRouter(prefix="/aml/risk", tags=["Risk Scoring"])


@router.post("/profiles", response_model=CustomerRiskProfile)
async def create_risk_profile(
    customer_id: str, customer_type: CustomerType, customer_name: str,
    country_of_residence: str = "US"
):
    """Create a new customer risk profile"""
    return await risk_scoring_service.create_risk_profile(
        customer_id, customer_type, customer_name,
        country_of_residence=country_of_residence
    )


@router.get("/profiles/{customer_id}", response_model=CustomerRiskProfile)
async def get_risk_profile(customer_id: str):
    """Get customer risk profile"""
    profile = await risk_scoring_service.get_risk_profile(customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/profiles/{customer_id}/assess", response_model=CustomerRiskAssessment)
async def assess_customer_risk(customer_id: str, assessment_type: str = "periodic"):
    """Perform customer risk assessment"""
    try:
        return await risk_scoring_service.assess_customer_risk(customer_id, assessment_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/profiles/{customer_id}/override")
async def request_risk_override(
    customer_id: str, requested_level: CustomerRiskLevel, reason: str,
    justification: str, requested_by: str = "system"
):
    """Request to override customer risk level"""
    try:
        return await risk_scoring_service.request_risk_override(
            customer_id, requested_level, reason, justification, requested_by
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/overrides/{override_id}/approve")
async def approve_override(override_id: UUID, approved_by: str, notes: str):
    """Approve a risk override request"""
    override = await risk_scoring_service.approve_override(override_id, approved_by, notes)
    if not override:
        raise HTTPException(status_code=404, detail="Override not found")
    return override


@router.get("/countries/{country_code}", response_model=GeographicRisk)
async def get_country_risk(country_code: str):
    """Get risk information for a country"""
    risk = await risk_scoring_service.get_country_risk(country_code)
    if not risk:
        raise HTTPException(status_code=404, detail="Country not found")
    return risk


@router.get("/countries/high-risk", response_model=List[GeographicRisk])
async def get_high_risk_countries():
    """Get list of high-risk countries"""
    return await risk_scoring_service.get_high_risk_countries()
