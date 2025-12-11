"""Interest Rate Routes - API endpoints for interest rate risk management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.interest_rate_models import (
    InterestRateCurve, DurationAnalysis, GapAnalysis, InterestRateScenario,
    BPVAnalysis, KeyRateDuration, CurveType, Currency
)
from ..services.interest_rate_service import interest_rate_service

router = APIRouter(prefix="/interest-rate", tags=["Interest Rate Risk"])


class CurveRequest(BaseModel):
    curve_name: str
    curve_type: CurveType
    currency: Currency
    tenors: List[str]
    rates: List[Decimal]


class DurationRequest(BaseModel):
    portfolio_id: UUID
    valuation_date: date


class GapAnalysisRequest(BaseModel):
    portfolio_id: UUID
    time_buckets: List[str]
    analysis_date: date


class ScenarioRequest(BaseModel):
    portfolio_id: UUID
    scenario_name: str
    parallel_shift: Optional[Decimal] = None
    curve_twist: Optional[Decimal] = None
    curve_butterfly: Optional[Decimal] = None


class BPVRequest(BaseModel):
    portfolio_id: UUID
    valuation_date: date


@router.post("/curves", response_model=InterestRateCurve)
async def create_curve(request: CurveRequest):
    """Create interest rate curve"""
    curve = await interest_rate_service.create_curve(
        curve_name=request.curve_name,
        curve_type=request.curve_type,
        currency=request.currency,
        tenors=request.tenors,
        rates=request.rates
    )
    return curve


@router.get("/curves/{curve_id}", response_model=InterestRateCurve)
async def get_curve(curve_id: UUID):
    """Get interest rate curve by ID"""
    curve = await interest_rate_service.get_curve(curve_id)
    if not curve:
        raise HTTPException(status_code=404, detail="Curve not found")
    return curve


@router.get("/curves", response_model=List[InterestRateCurve])
async def list_curves(
    currency: Optional[Currency] = Query(None),
    curve_type: Optional[CurveType] = Query(None)
):
    """List interest rate curves"""
    curves = await interest_rate_service.list_curves(currency, curve_type)
    return curves


@router.post("/duration", response_model=DurationAnalysis)
async def calculate_duration(request: DurationRequest):
    """Calculate duration analysis for portfolio"""
    analysis = await interest_rate_service.calculate_duration(
        portfolio_id=request.portfolio_id,
        valuation_date=request.valuation_date
    )
    return analysis


@router.get("/duration/{portfolio_id}", response_model=List[DurationAnalysis])
async def get_duration_history(portfolio_id: UUID):
    """Get duration analysis history for portfolio"""
    analyses = await interest_rate_service.get_duration_history(portfolio_id)
    return analyses


@router.post("/gap-analysis", response_model=GapAnalysis)
async def perform_gap_analysis(request: GapAnalysisRequest):
    """Perform gap analysis for portfolio"""
    analysis = await interest_rate_service.perform_gap_analysis(
        portfolio_id=request.portfolio_id,
        time_buckets=request.time_buckets,
        analysis_date=request.analysis_date
    )
    return analysis


@router.get("/gap-analysis/{portfolio_id}", response_model=List[GapAnalysis])
async def get_gap_analyses(portfolio_id: UUID):
    """Get gap analysis history for portfolio"""
    analyses = await interest_rate_service.get_gap_analyses(portfolio_id)
    return analyses


@router.post("/scenarios", response_model=InterestRateScenario)
async def create_scenario(request: ScenarioRequest):
    """Create interest rate scenario analysis"""
    scenario = await interest_rate_service.create_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        parallel_shift=request.parallel_shift,
        curve_twist=request.curve_twist,
        curve_butterfly=request.curve_butterfly
    )
    return scenario


@router.get("/scenarios/{portfolio_id}", response_model=List[InterestRateScenario])
async def get_scenarios(portfolio_id: UUID):
    """Get interest rate scenarios for portfolio"""
    scenarios = await interest_rate_service.get_scenarios(portfolio_id)
    return scenarios


@router.post("/bpv", response_model=BPVAnalysis)
async def calculate_bpv(request: BPVRequest):
    """Calculate Basis Point Value analysis"""
    analysis = await interest_rate_service.calculate_bpv(
        portfolio_id=request.portfolio_id,
        valuation_date=request.valuation_date
    )
    return analysis


@router.post("/key-rate-duration/{portfolio_id}", response_model=KeyRateDuration)
async def calculate_key_rate_duration(portfolio_id: UUID):
    """Calculate key rate durations for portfolio"""
    krd = await interest_rate_service.calculate_key_rate_duration(portfolio_id)
    return krd


@router.get("/statistics")
async def get_statistics():
    """Get interest rate risk statistics"""
    return await interest_rate_service.get_statistics()
