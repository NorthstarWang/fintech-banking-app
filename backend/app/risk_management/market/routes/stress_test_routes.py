"""Stress Test Routes - API endpoints for market risk stress testing"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.stress_test_models import (
    HistoricalScenario,
    ReverseStressTest,
    ScenarioSeverity,
    ScenarioType,
    SensitivityAnalysis,
    StressScenario,
    StressTestResult,
)
from ..services.stress_test_service import stress_test_service

router = APIRouter(prefix="/stress-test", tags=["Stress Testing"])


class ScenarioRequest(BaseModel):
    scenario_name: str
    scenario_type: ScenarioType
    severity: ScenarioSeverity
    description: str
    market_shocks: dict
    correlation_adjustments: dict | None = None


class StressTestRequest(BaseModel):
    portfolio_id: UUID
    scenario_id: UUID
    test_date: date


class HistoricalScenarioRequest(BaseModel):
    scenario_name: str
    event_start_date: date
    event_end_date: date
    description: str
    market_moves: dict


class SensitivityRequest(BaseModel):
    portfolio_id: UUID
    risk_factor: str
    shock_range: list[Decimal]
    analysis_date: date


class ReverseStressRequest(BaseModel):
    portfolio_id: UUID
    loss_threshold: Decimal
    risk_factors: list[str]


@router.post("/scenarios", response_model=StressScenario)
async def create_scenario(request: ScenarioRequest):
    """Create stress scenario"""
    return await stress_test_service.create_scenario(
        scenario_name=request.scenario_name,
        scenario_type=request.scenario_type,
        severity=request.severity,
        description=request.description,
        market_shocks=request.market_shocks,
        correlation_adjustments=request.correlation_adjustments
    )


@router.get("/scenarios/{scenario_id}", response_model=StressScenario)
async def get_scenario(scenario_id: UUID):
    """Get stress scenario by ID"""
    scenario = await stress_test_service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.get("/scenarios", response_model=list[StressScenario])
async def list_scenarios(
    scenario_type: ScenarioType | None = Query(None),
    severity: ScenarioSeverity | None = Query(None),
    is_active: bool | None = Query(True)
):
    """List stress scenarios"""
    return await stress_test_service.list_scenarios(
        scenario_type, severity, is_active
    )


@router.put("/scenarios/{scenario_id}/activate")
async def activate_scenario(scenario_id: UUID):
    """Activate stress scenario"""
    success = await stress_test_service.activate_scenario(scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"status": "activated"}


@router.put("/scenarios/{scenario_id}/deactivate")
async def deactivate_scenario(scenario_id: UUID):
    """Deactivate stress scenario"""
    success = await stress_test_service.deactivate_scenario(scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"status": "deactivated"}


@router.post("/run", response_model=StressTestResult)
async def run_stress_test(request: StressTestRequest):
    """Run stress test on portfolio"""
    return await stress_test_service.run_stress_test(
        portfolio_id=request.portfolio_id,
        scenario_id=request.scenario_id,
        test_date=request.test_date
    )


@router.post("/run-all/{portfolio_id}", response_model=list[StressTestResult])
async def run_all_scenarios(portfolio_id: UUID, test_date: date):
    """Run all active scenarios on portfolio"""
    return await stress_test_service.run_all_active_scenarios(
        portfolio_id, test_date
    )


@router.get("/results/{portfolio_id}", response_model=list[StressTestResult])
async def get_results(
    portfolio_id: UUID,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None)
):
    """Get stress test results for portfolio"""
    return await stress_test_service.get_results(
        portfolio_id, start_date, end_date
    )


@router.get("/results/{portfolio_id}/scenario/{scenario_id}", response_model=list[StressTestResult])
async def get_results_by_scenario(portfolio_id: UUID, scenario_id: UUID):
    """Get stress test results for specific scenario"""
    return await stress_test_service.get_results_by_scenario(
        portfolio_id, scenario_id
    )


@router.post("/historical", response_model=HistoricalScenario)
async def create_historical_scenario(request: HistoricalScenarioRequest):
    """Create historical scenario"""
    return await stress_test_service.create_historical_scenario(
        scenario_name=request.scenario_name,
        event_start_date=request.event_start_date,
        event_end_date=request.event_end_date,
        description=request.description,
        market_moves=request.market_moves
    )


@router.get("/historical", response_model=list[HistoricalScenario])
async def list_historical_scenarios():
    """List historical scenarios"""
    return await stress_test_service.list_historical_scenarios()


@router.post("/historical/{scenario_id}/replay/{portfolio_id}", response_model=StressTestResult)
async def replay_historical(scenario_id: UUID, portfolio_id: UUID):
    """Replay historical scenario on portfolio"""
    return await stress_test_service.replay_historical_scenario(
        scenario_id, portfolio_id
    )


@router.post("/sensitivity", response_model=SensitivityAnalysis)
async def run_sensitivity(request: SensitivityRequest):
    """Run sensitivity analysis"""
    return await stress_test_service.run_sensitivity_analysis(
        portfolio_id=request.portfolio_id,
        risk_factor=request.risk_factor,
        shock_range=request.shock_range,
        analysis_date=request.analysis_date
    )


@router.get("/sensitivity/{portfolio_id}", response_model=list[SensitivityAnalysis])
async def get_sensitivity_analyses(portfolio_id: UUID):
    """Get sensitivity analyses for portfolio"""
    return await stress_test_service.get_sensitivity_analyses(portfolio_id)


@router.post("/reverse", response_model=ReverseStressTest)
async def run_reverse_stress_test(request: ReverseStressRequest):
    """Run reverse stress test"""
    return await stress_test_service.run_reverse_stress_test(
        portfolio_id=request.portfolio_id,
        loss_threshold=request.loss_threshold,
        risk_factors=request.risk_factors
    )


@router.get("/reverse/{portfolio_id}", response_model=list[ReverseStressTest])
async def get_reverse_stress_tests(portfolio_id: UUID):
    """Get reverse stress tests for portfolio"""
    return await stress_test_service.get_reverse_stress_tests(portfolio_id)


@router.get("/statistics")
async def get_statistics():
    """Get stress testing statistics"""
    return await stress_test_service.get_statistics()
