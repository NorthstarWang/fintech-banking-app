"""Exposure Routes - API endpoints for exposure management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.exposure_models import (
    CreditExposure, ExposureAggregate, ExposureLimit,
    ExposureType, ExposureCategory
)
from ..services.exposure_service import exposure_service

router = APIRouter(prefix="/credit/exposures", tags=["Credit Exposures"])


class CreateExposureRequest(BaseModel):
    customer_id: str
    customer_name: str
    exposure_type: ExposureType
    exposure_category: ExposureCategory
    gross_exposure: float = Field(gt=0)
    limit_amount: float = Field(gt=0)
    collateral_value: float = Field(ge=0, default=0)


class UpdateExposureRequest(BaseModel):
    gross_exposure: Optional[float] = None
    collateral_value: Optional[float] = None
    limit_amount: Optional[float] = None


class SetLimitRequest(BaseModel):
    limit_type: str
    limit_key: str
    limit_name: str
    limit_amount: float = Field(gt=0)
    approved_by: str


class CheckLimitRequest(BaseModel):
    proposed_exposure: float = Field(gt=0)


class AggregateRequest(BaseModel):
    aggregation_level: str
    aggregation_key: str
    aggregation_name: str


class MovementRequest(BaseModel):
    movement_type: str
    change_amount: float
    change_reason: str


@router.post("/", response_model=CreditExposure)
async def create_exposure(request: CreateExposureRequest):
    """Create a new credit exposure"""
    exposure = await exposure_service.create_exposure(
        request.customer_id, request.customer_name,
        request.exposure_type, request.exposure_category,
        request.gross_exposure, request.limit_amount,
        request.collateral_value
    )
    return exposure


@router.get("/{exposure_id}", response_model=CreditExposure)
async def get_exposure(exposure_id: UUID):
    """Get exposure by ID"""
    exposure = await exposure_service.get_exposure(exposure_id)
    if not exposure:
        raise HTTPException(status_code=404, detail="Exposure not found")
    return exposure


@router.put("/{exposure_id}", response_model=CreditExposure)
async def update_exposure(exposure_id: UUID, request: UpdateExposureRequest):
    """Update an exposure"""
    updates = request.model_dump(exclude_none=True)
    exposure = await exposure_service.update_exposure(exposure_id, updates)
    if not exposure:
        raise HTTPException(status_code=404, detail="Exposure not found")
    return exposure


@router.get("/customer/{customer_id}", response_model=List[CreditExposure])
async def get_customer_exposures(customer_id: str):
    """Get all exposures for a customer"""
    return await exposure_service.get_customer_exposures(customer_id)


@router.post("/aggregate", response_model=ExposureAggregate)
async def calculate_aggregate(request: AggregateRequest):
    """Calculate exposure aggregate"""
    return await exposure_service.calculate_aggregate(
        request.aggregation_level, request.aggregation_key, request.aggregation_name
    )


@router.post("/limits", response_model=ExposureLimit)
async def set_limit(request: SetLimitRequest):
    """Set an exposure limit"""
    return await exposure_service.set_limit(
        request.limit_type, request.limit_key, request.limit_name,
        request.limit_amount, request.approved_by
    )


@router.get("/limits/{limit_id}", response_model=ExposureLimit)
async def get_limit(limit_id: UUID):
    """Get limit by ID"""
    limit = await exposure_service.get_limit(limit_id)
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    return limit


@router.post("/limits/{limit_id}/check")
async def check_limit(limit_id: UUID, request: CheckLimitRequest):
    """Check if proposed exposure is within limit"""
    return await exposure_service.check_limit(limit_id, request.proposed_exposure)


@router.post("/large-exposures")
async def identify_large_exposures(capital_base: float = Query(gt=0)):
    """Identify large exposures"""
    return await exposure_service.identify_large_exposures(capital_base)


@router.post("/{exposure_id}/movement")
async def record_movement(exposure_id: UUID, request: MovementRequest):
    """Record an exposure movement"""
    movement = await exposure_service.record_movement(
        exposure_id, request.movement_type, request.change_amount, request.change_reason
    )
    if not movement:
        raise HTTPException(status_code=404, detail="Exposure not found")
    return movement


@router.get("/")
async def list_exposures(
    exposure_type: Optional[ExposureType] = None,
    category: Optional[ExposureCategory] = None,
    limit: int = Query(default=100, le=500)
):
    """List exposures with optional filters"""
    return {"exposures": []}


@router.get("/statistics/summary")
async def get_exposure_statistics():
    """Get exposure statistics"""
    return await exposure_service.get_statistics()
