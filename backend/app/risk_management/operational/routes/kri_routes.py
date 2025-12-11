"""KRI Routes - API endpoints for Key Risk Indicators"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.kri_models import (
    KeyRiskIndicator, KRIMeasurement, KRIThresholdBreach, KRITarget,
    KRITrendAnalysis, KRIDashboard, KRIReport, KRIType, KRICategory
)
from ..services.kri_service import kri_service

router = APIRouter(prefix="/kri", tags=["Key Risk Indicators"])


class CreateKRIRequest(BaseModel):
    kri_name: str
    description: str
    kri_type: KRIType
    category: KRICategory
    business_unit: str
    owner: str
    measurement_unit: str
    measurement_frequency: str
    data_source: str
    calculation_method: str
    green_threshold_max: Optional[Decimal] = None
    amber_threshold_min: Optional[Decimal] = None
    amber_threshold_max: Optional[Decimal] = None
    red_threshold_min: Optional[Decimal] = None
    higher_is_worse: bool = True


class RecordMeasurementRequest(BaseModel):
    measurement_date: date
    measurement_period: str
    value: Decimal
    recorded_by: str
    notes: Optional[str] = None


class SetTargetRequest(BaseModel):
    target_period: str
    target_value: Decimal
    target_type: str
    effective_from: date
    approved_by: str
    rationale: Optional[str] = None


class ResolveBreachRequest(BaseModel):
    action_taken: str
    resolution_notes: str


@router.post("/", response_model=KeyRiskIndicator)
async def create_kri(request: CreateKRIRequest):
    """Create new KRI"""
    return await kri_service.create_kri(
        kri_name=request.kri_name,
        description=request.description,
        kri_type=request.kri_type,
        category=request.category,
        business_unit=request.business_unit,
        owner=request.owner,
        measurement_unit=request.measurement_unit,
        measurement_frequency=request.measurement_frequency,
        data_source=request.data_source,
        calculation_method=request.calculation_method,
        green_threshold_max=request.green_threshold_max,
        amber_threshold_min=request.amber_threshold_min,
        amber_threshold_max=request.amber_threshold_max,
        red_threshold_min=request.red_threshold_min,
        higher_is_worse=request.higher_is_worse
    )


@router.get("/{kri_id}", response_model=KeyRiskIndicator)
async def get_kri(kri_id: UUID):
    """Get KRI by ID"""
    kri = await kri_service.get_kri(kri_id)
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    return kri


@router.get("/code/{kri_code}", response_model=KeyRiskIndicator)
async def get_kri_by_code(kri_code: str):
    """Get KRI by code"""
    kri = await kri_service.get_kri_by_code(kri_code)
    if not kri:
        raise HTTPException(status_code=404, detail="KRI not found")
    return kri


@router.get("/", response_model=List[KeyRiskIndicator])
async def list_kris(
    category: Optional[KRICategory] = Query(None),
    business_unit: Optional[str] = Query(None),
    is_active: bool = Query(True)
):
    """List KRIs"""
    return await kri_service.list_kris(category, business_unit, is_active)


@router.post("/{kri_id}/measurements", response_model=KRIMeasurement)
async def record_measurement(kri_id: UUID, request: RecordMeasurementRequest):
    """Record KRI measurement"""
    return await kri_service.record_measurement(
        kri_id=kri_id,
        measurement_date=request.measurement_date,
        measurement_period=request.measurement_period,
        value=request.value,
        recorded_by=request.recorded_by,
        notes=request.notes
    )


@router.get("/{kri_id}/measurements", response_model=List[KRIMeasurement])
async def get_measurements(
    kri_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get KRI measurements"""
    return await kri_service.get_kri_measurements(kri_id, start_date, end_date)


@router.get("/breaches", response_model=List[KRIThresholdBreach])
async def get_breaches(
    kri_id: Optional[UUID] = Query(None),
    status: str = Query("open")
):
    """Get KRI breaches"""
    return await kri_service.get_kri_breaches(kri_id, status)


@router.put("/breaches/{breach_id}/resolve")
async def resolve_breach(breach_id: UUID, request: ResolveBreachRequest):
    """Resolve KRI breach"""
    breach = await kri_service.resolve_breach(
        breach_id, request.action_taken, request.resolution_notes
    )
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
    return breach


@router.post("/{kri_id}/targets", response_model=KRITarget)
async def set_target(kri_id: UUID, request: SetTargetRequest):
    """Set KRI target"""
    return await kri_service.set_target(
        kri_id=kri_id,
        target_period=request.target_period,
        target_value=request.target_value,
        target_type=request.target_type,
        effective_from=request.effective_from,
        approved_by=request.approved_by,
        rationale=request.rationale
    )


@router.post("/{kri_id}/trend-analysis", response_model=KRITrendAnalysis)
async def analyze_trend(
    kri_id: UUID,
    period_start: date,
    period_end: date
):
    """Analyze KRI trend"""
    return await kri_service.analyze_trend(kri_id, period_start, period_end)


@router.get("/dashboard", response_model=KRIDashboard)
async def get_dashboard(business_unit: Optional[str] = Query(None)):
    """Get KRI dashboard"""
    return await kri_service.generate_dashboard(business_unit)


@router.get("/statistics")
async def get_statistics():
    """Get KRI statistics"""
    return await kri_service.get_statistics()
