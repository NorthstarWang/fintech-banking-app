"""Regulatory Capital Management API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.capital_models import CapitalInstrumentType
from ..services.capital_service import capital_service

router = APIRouter(prefix="/capital", tags=["Regulatory Capital"])


class InstrumentRegistrationRequest(BaseModel):
    instrument_code: str
    instrument_type: CapitalInstrumentType
    tier: str
    issuer: str
    issue_date: date
    nominal_amount: Decimal
    carrying_amount: Decimal
    eligible_amount: Decimal
    maturity_date: Optional[date] = None
    coupon_rate: Optional[Decimal] = None


class DeductionRequest(BaseModel):
    reporting_date: date
    deduction_type: str
    tier: str
    gross_amount: Decimal
    deduction_amount: Decimal
    description: str
    reference: str
    methodology: str


class CapitalPlanRequest(BaseModel):
    plan_name: str
    plan_year: int
    entity_id: str
    baseline_capital: Decimal
    target_cet1_ratio: Decimal
    target_tier1_ratio: Decimal
    target_total_ratio: Decimal
    planned_issuances: List[Dict[str, Any]]
    planned_redemptions: List[Dict[str, Any]]


class StressTestRequest(BaseModel):
    scenario_name: str
    scenario_type: str
    starting_capital: Decimal
    credit_losses: Decimal
    market_losses: Decimal
    operational_losses: Decimal


class CapitalLimitRequest(BaseModel):
    limit_type: str
    metric: str
    minimum_value: Decimal
    warning_threshold: Decimal
    target_value: Decimal
    approved_by: str


@router.post("/instruments", response_model=dict)
async def register_instrument(request: InstrumentRegistrationRequest):
    """Register a new capital instrument"""
    instrument = await capital_service.register_instrument(
        instrument_code=request.instrument_code, instrument_type=request.instrument_type,
        tier=request.tier, issuer=request.issuer, issue_date=request.issue_date,
        nominal_amount=request.nominal_amount, carrying_amount=request.carrying_amount,
        eligible_amount=request.eligible_amount, maturity_date=request.maturity_date,
        coupon_rate=request.coupon_rate
    )
    return {"instrument_id": str(instrument.instrument_id), "tier": instrument.tier}


@router.get("/instruments", response_model=List[dict])
async def list_instruments(tier: Optional[str] = None, active_only: bool = True):
    """List capital instruments"""
    if tier:
        instruments = await capital_service.repository.find_instruments_by_tier(tier)
    elif active_only:
        instruments = await capital_service.repository.find_active_instruments()
    else:
        instruments = await capital_service.repository.find_all_instruments()
    return [{"instrument_id": str(i.instrument_id), "instrument_code": i.instrument_code, "tier": i.tier, "eligible_amount": float(i.eligible_amount)} for i in instruments]


@router.get("/instruments/{instrument_id}", response_model=dict)
async def get_instrument(instrument_id: UUID):
    """Get a specific capital instrument"""
    instrument = await capital_service.repository.find_instrument_by_id(instrument_id)
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return {
        "instrument_id": str(instrument.instrument_id),
        "instrument_code": instrument.instrument_code,
        "instrument_type": instrument.instrument_type.value,
        "tier": instrument.tier,
        "nominal_amount": float(instrument.nominal_amount),
        "eligible_amount": float(instrument.eligible_amount)
    }


@router.post("/deductions", response_model=dict)
async def record_deduction(request: DeductionRequest):
    """Record a capital deduction"""
    deduction = await capital_service.record_deduction(
        reporting_date=request.reporting_date, deduction_type=request.deduction_type,
        tier=request.tier, gross_amount=request.gross_amount,
        deduction_amount=request.deduction_amount, description=request.description,
        reference=request.reference, methodology=request.methodology
    )
    return {"deduction_id": str(deduction.deduction_id), "tier": deduction.tier}


@router.get("/deductions", response_model=List[dict])
async def list_deductions(reporting_date: Optional[date] = None, tier: Optional[str] = None):
    """List capital deductions"""
    if reporting_date:
        deductions = await capital_service.repository.find_deductions_by_date(reporting_date)
    elif tier:
        deductions = await capital_service.repository.find_deductions_by_tier(tier)
    else:
        deductions = await capital_service.repository.find_all_deductions()
    return [{"deduction_id": str(d.deduction_id), "tier": d.tier, "deduction_amount": float(d.deduction_amount)} for d in deductions]


@router.post("/positions/calculate", response_model=dict)
async def calculate_capital_position(
    reporting_date: date = Query(...),
    entity_id: str = Query(...)
):
    """Calculate current capital position"""
    position = await capital_service.calculate_capital_position(
        reporting_date=reporting_date, entity_id=entity_id
    )
    return {
        "position_id": str(position.position_id),
        "cet1_ratio": float(position.cet1_ratio),
        "tier1_ratio": float(position.tier1_ratio),
        "total_capital_ratio": float(position.total_capital_ratio),
        "leverage_ratio": float(position.leverage_ratio),
        "total_capital": float(position.total_capital)
    }


@router.get("/positions/{entity_id}/latest", response_model=dict)
async def get_latest_position(entity_id: str):
    """Get latest capital position for an entity"""
    position = await capital_service.repository.find_latest_position(entity_id)
    if not position:
        raise HTTPException(status_code=404, detail="No capital position found")
    return {
        "position_id": str(position.position_id),
        "reporting_date": str(position.reporting_date),
        "cet1_ratio": float(position.cet1_ratio),
        "tier1_ratio": float(position.tier1_ratio),
        "total_capital_ratio": float(position.total_capital_ratio)
    }


@router.post("/plans", response_model=dict)
async def create_capital_plan(request: CapitalPlanRequest):
    """Create a capital plan"""
    plan = await capital_service.create_capital_plan(
        plan_name=request.plan_name, plan_year=request.plan_year, entity_id=request.entity_id,
        baseline_capital=request.baseline_capital, target_cet1_ratio=request.target_cet1_ratio,
        target_tier1_ratio=request.target_tier1_ratio, target_total_ratio=request.target_total_ratio,
        planned_issuances=request.planned_issuances, planned_redemptions=request.planned_redemptions
    )
    return {"plan_id": str(plan.plan_id), "plan_name": plan.plan_name}


@router.get("/plans", response_model=List[dict])
async def list_capital_plans(year: Optional[int] = None, approved_only: bool = False):
    """List capital plans"""
    if year:
        plans = await capital_service.repository.find_plans_by_year(year)
    elif approved_only:
        plans = await capital_service.repository.find_approved_plans()
    else:
        plans = await capital_service.repository.find_all_plans()
    return [{"plan_id": str(p.plan_id), "plan_name": p.plan_name, "plan_year": p.plan_year, "status": p.status} for p in plans]


@router.post("/stress-tests", response_model=dict)
async def run_stress_test(request: StressTestRequest):
    """Run a capital stress test"""
    stress = await capital_service.run_stress_test(
        scenario_name=request.scenario_name, scenario_type=request.scenario_type,
        starting_capital=request.starting_capital, credit_losses=request.credit_losses,
        market_losses=request.market_losses, operational_losses=request.operational_losses
    )
    return {
        "stress_test_id": str(stress.stress_test_id),
        "projected_capital": float(stress.projected_capital),
        "capital_impact": float(stress.capital_impact),
        "capital_shortfall": float(stress.capital_shortfall)
    }


@router.get("/stress-tests", response_model=List[dict])
async def list_stress_tests(scenario_type: Optional[str] = None):
    """List capital stress tests"""
    if scenario_type:
        tests = await capital_service.repository.find_stress_tests_by_scenario(scenario_type)
    else:
        tests = await capital_service.repository.find_all_stress_tests()
    return [{"stress_test_id": str(s.stress_test_id), "scenario_name": s.scenario_name, "capital_impact": float(s.capital_impact)} for s in tests]


@router.post("/limits", response_model=dict)
async def set_capital_limit(request: CapitalLimitRequest):
    """Set a capital limit"""
    limit = await capital_service.set_capital_limit(
        limit_type=request.limit_type, metric=request.metric,
        minimum_value=request.minimum_value, warning_threshold=request.warning_threshold,
        target_value=request.target_value, approved_by=request.approved_by
    )
    return {"limit_id": str(limit.limit_id), "status": limit.status}


@router.get("/limits/breached", response_model=List[dict])
async def list_breached_limits():
    """List breached capital limits"""
    limits = await capital_service.repository.find_breached_limits()
    return [{"limit_id": str(l.limit_id), "metric": l.metric, "current_value": float(l.current_value), "minimum_value": float(l.minimum_value)} for l in limits]


@router.post("/reports/generate", response_model=dict)
async def generate_capital_report(entity_id: str = Query(...), generated_by: str = Query(...)):
    """Generate a capital report"""
    report = await capital_service.generate_report(entity_id=entity_id, generated_by=generated_by)
    return {"report_id": str(report.report_id), "report_date": str(report.report_date)}


@router.get("/statistics", response_model=dict)
async def get_capital_statistics():
    """Get capital management statistics"""
    return await capital_service.get_statistics()
