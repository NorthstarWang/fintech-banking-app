"""Collateral Routes - API endpoints for collateral management"""

from typing import Optional, List
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.collateral_models import (
    Collateral, CollateralValuation, CollateralAllocation, Guarantee,
    CollateralType, CollateralStatus, ValuationType
)
from ..services.collateral_service import collateral_service

router = APIRouter(prefix="/credit/collateral", tags=["Credit Collateral"])


class RegisterCollateralRequest(BaseModel):
    collateral_type: CollateralType
    description: str
    owner_id: str
    owner_name: str
    original_value: float = Field(gt=0)


class RecordValuationRequest(BaseModel):
    valuation_type: ValuationType
    market_value: float = Field(gt=0)
    forced_sale_value: float = Field(gt=0)
    valuer_name: str
    methodology: str


class AllocateRequest(BaseModel):
    facility_id: UUID
    allocation_amount: float = Field(gt=0)
    priority_ranking: int = Field(ge=1, default=1)


class MonitorRequest(BaseModel):
    monitored_by: str


class GuaranteeRequest(BaseModel):
    guarantee_type: str
    guarantor_id: str
    guarantor_name: str
    guaranteed_facility_id: UUID
    guarantee_amount: float = Field(gt=0)
    effective_date: date
    expiry_date: date


@router.post("/", response_model=Collateral)
async def register_collateral(request: RegisterCollateralRequest):
    """Register new collateral"""
    collateral = await collateral_service.register_collateral(
        request.collateral_type, request.description,
        request.owner_id, request.owner_name, request.original_value
    )
    return collateral


@router.get("/{collateral_id}", response_model=Collateral)
async def get_collateral(collateral_id: UUID):
    """Get collateral by ID"""
    collateral = await collateral_service.get_collateral(collateral_id)
    if not collateral:
        raise HTTPException(status_code=404, detail="Collateral not found")
    return collateral


@router.post("/{collateral_id}/valuations", response_model=CollateralValuation)
async def record_valuation(collateral_id: UUID, request: RecordValuationRequest):
    """Record a collateral valuation"""
    valuation = await collateral_service.record_valuation(
        collateral_id, request.valuation_type, request.market_value,
        request.forced_sale_value, request.valuer_name, request.methodology
    )
    if not valuation:
        raise HTTPException(status_code=404, detail="Collateral not found")
    return valuation


@router.post("/{collateral_id}/allocate", response_model=CollateralAllocation)
async def allocate_collateral(collateral_id: UUID, request: AllocateRequest):
    """Allocate collateral to a facility"""
    allocation = await collateral_service.allocate_collateral(
        collateral_id, request.facility_id,
        request.allocation_amount, request.priority_ranking
    )
    if not allocation:
        raise HTTPException(status_code=400, detail="Cannot allocate - insufficient value")
    return allocation


@router.post("/allocations/{allocation_id}/release")
async def release_allocation(allocation_id: UUID):
    """Release a collateral allocation"""
    success = await collateral_service.release_allocation(allocation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return {"message": "Allocation released successfully"}


@router.post("/{collateral_id}/monitor")
async def monitor_collateral(collateral_id: UUID, request: MonitorRequest):
    """Monitor collateral"""
    monitoring = await collateral_service.monitor_collateral(
        collateral_id, request.monitored_by
    )
    if not monitoring:
        raise HTTPException(status_code=404, detail="Collateral not found")
    return monitoring


@router.post("/guarantees", response_model=Guarantee)
async def register_guarantee(request: GuaranteeRequest):
    """Register a guarantee"""
    guarantee = await collateral_service.register_guarantee(
        request.guarantee_type, request.guarantor_id, request.guarantor_name,
        request.guaranteed_facility_id, request.guarantee_amount,
        request.effective_date, request.expiry_date
    )
    return guarantee


@router.get("/customer/{customer_id}", response_model=List[Collateral])
async def get_customer_collaterals(customer_id: str):
    """Get all collateral for a customer"""
    return await collateral_service.get_customer_collaterals(customer_id)


@router.get("/")
async def list_collaterals(
    collateral_type: Optional[CollateralType] = None,
    status: Optional[CollateralStatus] = None,
    limit: int = Query(default=100, le=500)
):
    """List collaterals with optional filters"""
    return {"collaterals": []}


@router.get("/statistics/summary")
async def get_collateral_statistics():
    """Get collateral statistics"""
    return await collateral_service.get_statistics()
