"""Equity Risk Routes - API endpoints for equity risk management"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.equity_risk_models import (
    BetaAnalysis,
    EquityExposure,
    EquityFactorExposure,
    EquityPosition,
    EquityScenario,
    EquitySector,
    IndexBenchmark,
)
from ..services.equity_risk_service import equity_risk_service

router = APIRouter(prefix="/equity-risk", tags=["Equity Risk"])


class EquityPositionRequest(BaseModel):
    portfolio_id: UUID
    ticker: str
    quantity: Decimal
    price: Decimal
    sector: EquitySector
    country: str
    currency: str


class BetaAnalysisRequest(BaseModel):
    portfolio_id: UUID
    benchmark: IndexBenchmark
    lookback_days: int = 252


class FactorExposureRequest(BaseModel):
    portfolio_id: UUID
    factor_model: str
    analysis_date: date


class ScenarioRequest(BaseModel):
    portfolio_id: UUID
    scenario_name: str
    market_shock: Decimal
    sector_shocks: dict | None = None


class ExposureRequest(BaseModel):
    portfolio_id: UUID
    exposure_type: str
    analysis_date: date


@router.post("/positions", response_model=EquityPosition)
async def create_position(request: EquityPositionRequest):
    """Create equity position"""
    return await equity_risk_service.create_position(
        portfolio_id=request.portfolio_id,
        ticker=request.ticker,
        quantity=request.quantity,
        price=request.price,
        sector=request.sector,
        country=request.country,
        currency=request.currency
    )


@router.get("/positions/{position_id}", response_model=EquityPosition)
async def get_position(position_id: UUID):
    """Get equity position by ID"""
    position = await equity_risk_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/positions", response_model=list[EquityPosition])
async def list_positions(
    portfolio_id: UUID | None = Query(None),
    sector: EquitySector | None = Query(None),
    ticker: str | None = Query(None)
):
    """List equity positions"""
    return await equity_risk_service.list_positions(portfolio_id, sector, ticker)


@router.put("/positions/{position_id}", response_model=EquityPosition)
async def update_position(position_id: UUID, price: Decimal):
    """Update equity position price"""
    position = await equity_risk_service.update_position_price(position_id, price)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.delete("/positions/{position_id}")
async def close_position(position_id: UUID):
    """Close equity position"""
    success = await equity_risk_service.close_position(position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"status": "closed"}


@router.post("/beta-analysis", response_model=BetaAnalysis)
async def calculate_beta(request: BetaAnalysisRequest):
    """Calculate portfolio beta"""
    return await equity_risk_service.calculate_beta(
        portfolio_id=request.portfolio_id,
        benchmark=request.benchmark,
        lookback_days=request.lookback_days
    )


@router.get("/beta-analysis/{portfolio_id}", response_model=list[BetaAnalysis])
async def get_beta_history(portfolio_id: UUID):
    """Get beta analysis history for portfolio"""
    return await equity_risk_service.get_beta_history(portfolio_id)


@router.post("/factor-exposure", response_model=EquityFactorExposure)
async def calculate_factor_exposure(request: FactorExposureRequest):
    """Calculate factor exposures"""
    return await equity_risk_service.calculate_factor_exposure(
        portfolio_id=request.portfolio_id,
        factor_model=request.factor_model,
        analysis_date=request.analysis_date
    )


@router.get("/factor-exposure/{portfolio_id}", response_model=list[EquityFactorExposure])
async def get_factor_exposures(portfolio_id: UUID):
    """Get factor exposure history for portfolio"""
    return await equity_risk_service.get_factor_exposures(portfolio_id)


@router.post("/exposures", response_model=EquityExposure)
async def calculate_exposure(request: ExposureRequest):
    """Calculate equity exposure"""
    return await equity_risk_service.calculate_exposure(
        portfolio_id=request.portfolio_id,
        exposure_type=request.exposure_type,
        analysis_date=request.analysis_date
    )


@router.get("/exposures/{portfolio_id}", response_model=list[EquityExposure])
async def get_exposures(portfolio_id: UUID):
    """Get equity exposures for portfolio"""
    return await equity_risk_service.get_exposures(portfolio_id)


@router.post("/scenarios", response_model=EquityScenario)
async def run_scenario(request: ScenarioRequest):
    """Run equity scenario analysis"""
    return await equity_risk_service.run_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        market_shock=request.market_shock,
        sector_shocks=request.sector_shocks
    )


@router.get("/scenarios/{portfolio_id}", response_model=list[EquityScenario])
async def get_scenarios(portfolio_id: UUID):
    """Get equity scenarios for portfolio"""
    return await equity_risk_service.get_scenarios(portfolio_id)


@router.get("/sector-breakdown/{portfolio_id}")
async def get_sector_breakdown(portfolio_id: UUID):
    """Get sector breakdown for portfolio"""
    return await equity_risk_service.get_sector_breakdown(portfolio_id)


@router.get("/country-breakdown/{portfolio_id}")
async def get_country_breakdown(portfolio_id: UUID):
    """Get country breakdown for portfolio"""
    return await equity_risk_service.get_country_breakdown(portfolio_id)


@router.get("/statistics")
async def get_statistics():
    """Get equity risk statistics"""
    return await equity_risk_service.get_statistics()
