"""Interest Rate Routes - API endpoints for interest rate risk management"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.interest_rate_models import (
    BPVAnalysis,
    Currency,
    CurveType,
    DurationAnalysis,
    GapAnalysis,
    InterestRateCurve,
    InterestRateScenario,
    KeyRateDuration,
)
from ..services.interest_rate_service import interest_rate_service

router = APIRouter(prefix="/interest-rate", tags=["Interest Rate Risk"])


class CurveRequest(BaseModel):
    curve_name: str
    curve_type: CurveType
    currency: Currency
    tenors: list[str]
    rates: list[Decimal]


class DurationRequest(BaseModel):
    portfolio_id: UUID
    valuation_date: date


class GapAnalysisRequest(BaseModel):
    portfolio_id: UUID
    time_buckets: list[str]
    analysis_date: date


class ScenarioRequest(BaseModel):
    portfolio_id: UUID
    scenario_name: str
    parallel_shift: Decimal | None = None
    curve_twist: Decimal | None = None
    curve_butterfly: Decimal | None = None


class BPVRequest(BaseModel):
    portfolio_id: UUID
    valuation_date: date


@router.post("/curves", response_model=InterestRateCurve)
async def create_curve(request: CurveRequest):
    """Create interest rate curve"""
    return await interest_rate_service.create_curve(
        curve_name=request.curve_name,
        curve_type=request.curve_type,
        currency=request.currency,
        tenors=request.tenors,
        rates=request.rates
    )


@router.get("/curves/{curve_id}", response_model=InterestRateCurve)
async def get_curve(curve_id: UUID):
    """Get interest rate curve by ID"""
    curve = await interest_rate_service.get_curve(curve_id)
    if not curve:
        raise HTTPException(status_code=404, detail="Curve not found")
    return curve


@router.get("/curves", response_model=list[InterestRateCurve])
async def list_curves(
    currency: Currency | None = Query(None),
    curve_type: CurveType | None = Query(None)
):
    """List interest rate curves"""
    return await interest_rate_service.list_curves(currency, curve_type)


@router.post("/duration", response_model=DurationAnalysis)
async def calculate_duration(request: DurationRequest):
    """Calculate duration analysis for portfolio"""
    return await interest_rate_service.calculate_duration(
        portfolio_id=request.portfolio_id,
        valuation_date=request.valuation_date
    )


@router.get("/duration/{portfolio_id}", response_model=list[DurationAnalysis])
async def get_duration_history(portfolio_id: UUID):
    """Get duration analysis history for portfolio"""
    return await interest_rate_service.get_duration_history(portfolio_id)


@router.post("/gap-analysis", response_model=GapAnalysis)
async def perform_gap_analysis(request: GapAnalysisRequest):
    """Perform gap analysis for portfolio"""
    return await interest_rate_service.perform_gap_analysis(
        portfolio_id=request.portfolio_id,
        time_buckets=request.time_buckets,
        analysis_date=request.analysis_date
    )


@router.get("/gap-analysis/{portfolio_id}", response_model=list[GapAnalysis])
async def get_gap_analyses(portfolio_id: UUID):
    """Get gap analysis history for portfolio"""
    return await interest_rate_service.get_gap_analyses(portfolio_id)


@router.post("/scenarios", response_model=InterestRateScenario)
async def create_scenario(request: ScenarioRequest):
    """Create interest rate scenario analysis"""
    return await interest_rate_service.create_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        parallel_shift=request.parallel_shift,
        curve_twist=request.curve_twist,
        curve_butterfly=request.curve_butterfly
    )


@router.get("/scenarios/{portfolio_id}", response_model=list[InterestRateScenario])
async def get_scenarios(portfolio_id: UUID):
    """Get interest rate scenarios for portfolio"""
    return await interest_rate_service.get_scenarios(portfolio_id)


@router.post("/bpv", response_model=BPVAnalysis)
async def calculate_bpv(request: BPVRequest):
    """Calculate Basis Point Value analysis"""
    return await interest_rate_service.calculate_bpv(
        portfolio_id=request.portfolio_id,
        valuation_date=request.valuation_date
    )


@router.post("/key-rate-duration/{portfolio_id}", response_model=KeyRateDuration)
async def calculate_key_rate_duration(portfolio_id: UUID):
    """Calculate key rate durations for portfolio"""
    return await interest_rate_service.calculate_key_rate_duration(portfolio_id)


@router.get("/statistics")
async def get_statistics():
    """Get interest rate risk statistics"""
    return await interest_rate_service.get_statistics()
