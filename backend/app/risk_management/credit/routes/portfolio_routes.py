"""Portfolio Routes - API endpoints for portfolio management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.portfolio_models import (
    CreditPortfolio, PortfolioSegment, ConcentrationRisk,
    PortfolioType, PortfolioStatus, ConcentrationRiskType
)
from ..services.portfolio_service import portfolio_service

router = APIRouter(prefix="/credit/portfolios", tags=["Credit Portfolios"])


class CreatePortfolioRequest(BaseModel):
    name: str
    portfolio_type: PortfolioType
    description: str
    manager: str


class UpdateMetricsRequest(BaseModel):
    total_exposure: Optional[float] = None
    expected_loss: Optional[float] = None
    weighted_average_pd: Optional[float] = None
    weighted_average_lgd: Optional[float] = None


class AddSegmentRequest(BaseModel):
    segment_name: str
    segment_type: str
    exposure_amount: float


class ConcentrationRequest(BaseModel):
    concentration_type: ConcentrationRiskType
    dimension_name: str
    dimension_value: str
    exposure_amount: float
    limit_percentage: Optional[float] = None


class StressTestRequest(BaseModel):
    scenario_name: str
    scenario_type: str
    economic_assumptions: Dict[str, float]
    created_by: str


class MigrationRequest(BaseModel):
    period_start: date
    period_end: date


@router.post("/", response_model=CreditPortfolio)
async def create_portfolio(request: CreatePortfolioRequest):
    """Create a new credit portfolio"""
    portfolio = await portfolio_service.create_portfolio(
        request.name, request.portfolio_type, request.description, request.manager
    )
    return portfolio


@router.get("/{portfolio_id}", response_model=CreditPortfolio)
async def get_portfolio(portfolio_id: UUID):
    """Get portfolio by ID"""
    portfolio = await portfolio_service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.put("/{portfolio_id}/metrics", response_model=CreditPortfolio)
async def update_metrics(portfolio_id: UUID, request: UpdateMetricsRequest):
    """Update portfolio metrics"""
    metrics = request.model_dump(exclude_none=True)
    portfolio = await portfolio_service.update_portfolio_metrics(portfolio_id, metrics)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.post("/{portfolio_id}/segments", response_model=PortfolioSegment)
async def add_segment(portfolio_id: UUID, request: AddSegmentRequest):
    """Add a segment to portfolio"""
    segment = await portfolio_service.add_segment(
        portfolio_id, request.segment_name, request.segment_type, request.exposure_amount
    )
    if not segment:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return segment


@router.get("/{portfolio_id}/segments", response_model=List[PortfolioSegment])
async def get_segments(portfolio_id: UUID):
    """Get portfolio segments"""
    return await portfolio_service.get_portfolio_segments(portfolio_id)


@router.post("/{portfolio_id}/concentration", response_model=ConcentrationRisk)
async def assess_concentration(portfolio_id: UUID, request: ConcentrationRequest):
    """Assess concentration risk"""
    concentration = await portfolio_service.assess_concentration_risk(
        portfolio_id, request.concentration_type, request.dimension_name,
        request.dimension_value, request.exposure_amount, request.limit_percentage
    )
    if not concentration:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return concentration


@router.get("/{portfolio_id}/concentration", response_model=List[ConcentrationRisk])
async def get_concentrations(portfolio_id: UUID):
    """Get portfolio concentration risks"""
    return await portfolio_service.get_concentration_risks(portfolio_id)


@router.post("/{portfolio_id}/migration")
async def calculate_migration(portfolio_id: UUID, request: MigrationRequest):
    """Calculate rating migration matrix"""
    migration = await portfolio_service.calculate_migration_matrix(
        portfolio_id, request.period_start, request.period_end
    )
    if not migration:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return migration


@router.post("/{portfolio_id}/stress-test")
async def run_stress_test(portfolio_id: UUID, request: StressTestRequest):
    """Run portfolio stress test"""
    result = await portfolio_service.run_stress_test(
        portfolio_id, request.scenario_name, request.scenario_type,
        request.economic_assumptions, request.created_by
    )
    if not result:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return result


@router.get("/")
async def list_portfolios(
    portfolio_type: Optional[PortfolioType] = None,
    status: Optional[PortfolioStatus] = None,
    limit: int = Query(default=100, le=500)
):
    """List portfolios with optional filters"""
    return {"portfolios": []}


@router.get("/statistics/summary")
async def get_portfolio_statistics():
    """Get portfolio statistics"""
    return await portfolio_service.get_statistics()
