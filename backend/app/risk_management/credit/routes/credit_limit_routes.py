"""Credit Limit Routes - API endpoints for credit limit management"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.credit_limit_models import (
    CreditLimit, LimitRequest, LimitReview, LimitBreach, LimitCovenant,
    LimitType, LimitStatus
)
from ..services.credit_limit_service import credit_limit_service

router = APIRouter(prefix="/credit/limits", tags=["Credit Limits"])


class CreateLimitRequest(BaseModel):
    limit_type: LimitType
    entity_id: str
    entity_name: str
    limit_amount: float = Field(gt=0)
    tenor_months: int = Field(gt=0, le=120)
    approved_by: str
    conditions: List[str] = []


class UtilizeLimitRequest(BaseModel):
    amount: float = Field(gt=0)
    utilization_type: str
    transaction_reference: Optional[str] = None


class SubmitRequestRequest(BaseModel):
    request_type: str
    limit_type: LimitType
    entity_id: str
    entity_name: str
    requested_limit: float = Field(gt=0)
    tenor_months: int = Field(gt=0)
    purpose: str
    justification: str
    requested_by: str


class ApproveRequestRequest(BaseModel):
    approved_amount: float = Field(gt=0)
    conditions: List[str] = []
    approved_by: str


class CreateReviewRequest(BaseModel):
    review_type: str
    recommended_limit: float = Field(gt=0)
    recommendation: str
    reviewed_by: str


class AddCovenantRequest(BaseModel):
    covenant_type: str
    covenant_name: str
    description: str
    threshold_value: float
    measurement_frequency: str


@router.post("/", response_model=CreditLimit)
async def create_limit(request: CreateLimitRequest):
    """Create a new credit limit"""
    limit = await credit_limit_service.create_limit(
        request.limit_type, request.entity_id, request.entity_name,
        request.limit_amount, request.tenor_months, request.approved_by,
        request.conditions
    )
    return limit


@router.get("/{limit_id}", response_model=CreditLimit)
async def get_limit(limit_id: UUID):
    """Get limit by ID"""
    limit = await credit_limit_service.get_limit(limit_id)
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    return limit


@router.get("/entity/{entity_id}")
async def get_entity_limit(entity_id: str, limit_type: Optional[LimitType] = None):
    """Get limit for an entity"""
    limit = await credit_limit_service.get_entity_limit(entity_id, limit_type)
    if not limit:
        raise HTTPException(status_code=404, detail="No limit found for entity")
    return limit


@router.post("/{limit_id}/utilize")
async def utilize_limit(limit_id: UUID, request: UtilizeLimitRequest):
    """Utilize a credit limit"""
    utilization = await credit_limit_service.utilize_limit(
        limit_id, request.amount, request.utilization_type, request.transaction_reference
    )
    if not utilization:
        raise HTTPException(status_code=400, detail="Cannot utilize - limit exceeded or not found")
    return utilization


@router.post("/requests", response_model=LimitRequest)
async def submit_request(request: SubmitRequestRequest):
    """Submit a limit request"""
    limit_request = await credit_limit_service.submit_limit_request(
        request.request_type, request.limit_type, request.entity_id,
        request.entity_name, request.requested_limit, request.tenor_months,
        request.purpose, request.justification, request.requested_by
    )
    return limit_request


@router.post("/requests/{request_id}/approve", response_model=LimitRequest)
async def approve_request(request_id: UUID, request: ApproveRequestRequest):
    """Approve a limit request"""
    limit_request = await credit_limit_service.approve_request(
        request_id, request.approved_amount, request.conditions, request.approved_by
    )
    if not limit_request:
        raise HTTPException(status_code=404, detail="Request not found")
    return limit_request


@router.post("/{limit_id}/reviews", response_model=LimitReview)
async def create_review(limit_id: UUID, request: CreateReviewRequest):
    """Create a limit review"""
    review = await credit_limit_service.create_review(
        limit_id, request.review_type, request.recommended_limit,
        request.recommendation, request.reviewed_by
    )
    if not review:
        raise HTTPException(status_code=404, detail="Limit not found")
    return review


@router.post("/{limit_id}/covenants", response_model=LimitCovenant)
async def add_covenant(limit_id: UUID, request: AddCovenantRequest):
    """Add a covenant to a limit"""
    covenant = await credit_limit_service.add_covenant(
        limit_id, request.covenant_type, request.covenant_name,
        request.description, request.threshold_value, request.measurement_frequency
    )
    if not covenant:
        raise HTTPException(status_code=404, detail="Limit not found")
    return covenant


@router.get("/{limit_id}/breaches", response_model=List[LimitBreach])
async def get_breaches(limit_id: UUID):
    """Get breaches for a limit"""
    return await credit_limit_service.get_breaches(limit_id)


@router.get("/breaches/all", response_model=List[LimitBreach])
async def get_all_breaches():
    """Get all limit breaches"""
    return await credit_limit_service.get_breaches()


@router.get("/")
async def list_limits(
    limit_type: Optional[LimitType] = None,
    status: Optional[LimitStatus] = None,
    limit: int = Query(default=100, le=500)
):
    """List limits with optional filters"""
    return {"limits": []}


@router.get("/statistics/summary")
async def get_limit_statistics():
    """Get limit statistics"""
    return await credit_limit_service.get_statistics()
