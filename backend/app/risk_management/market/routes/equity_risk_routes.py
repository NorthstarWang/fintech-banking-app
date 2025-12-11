"""Equity Risk Routes - API endpoints for equity risk management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.equity_risk_models import (
    EquityPosition, EquityExposure, BetaAnalysis, EquityFactorExposure,
    EquityScenario, EquitySector, IndexBenchmark
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
    sector_shocks: Optional[dict] = None


class ExposureRequest(BaseModel):
    portfolio_id: UUID
    exposure_type: str
    analysis_date: date


@router.post("/positions", response_model=EquityPosition)
async def create_position(request: EquityPositionRequest):
    """Create equity position"""
    position = await equity_risk_service.create_position(
        portfolio_id=request.portfolio_id,
        ticker=request.ticker,
        quantity=request.quantity,
        price=request.price,
        sector=request.sector,
        country=request.country,
        currency=request.currency
    )
    return position


@router.get("/positions/{position_id}", response_model=EquityPosition)
async def get_position(position_id: UUID):
    """Get equity position by ID"""
    position = await equity_risk_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/positions", response_model=List[EquityPosition])
async def list_positions(
    portfolio_id: Optional[UUID] = Query(None),
    sector: Optional[EquitySector] = Query(None),
    ticker: Optional[str] = Query(None)
):
    """List equity positions"""
    positions = await equity_risk_service.list_positions(portfolio_id, sector, ticker)
    return positions


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
    analysis = await equity_risk_service.calculate_beta(
        portfolio_id=request.portfolio_id,
        benchmark=request.benchmark,
        lookback_days=request.lookback_days
    )
    return analysis


@router.get("/beta-analysis/{portfolio_id}", response_model=List[BetaAnalysis])
async def get_beta_history(portfolio_id: UUID):
    """Get beta analysis history for portfolio"""
    analyses = await equity_risk_service.get_beta_history(portfolio_id)
    return analyses


@router.post("/factor-exposure", response_model=EquityFactorExposure)
async def calculate_factor_exposure(request: FactorExposureRequest):
    """Calculate factor exposures"""
    exposure = await equity_risk_service.calculate_factor_exposure(
        portfolio_id=request.portfolio_id,
        factor_model=request.factor_model,
        analysis_date=request.analysis_date
    )
    return exposure


@router.get("/factor-exposure/{portfolio_id}", response_model=List[EquityFactorExposure])
async def get_factor_exposures(portfolio_id: UUID):
    """Get factor exposure history for portfolio"""
    exposures = await equity_risk_service.get_factor_exposures(portfolio_id)
    return exposures


@router.post("/exposures", response_model=EquityExposure)
async def calculate_exposure(request: ExposureRequest):
    """Calculate equity exposure"""
    exposure = await equity_risk_service.calculate_exposure(
        portfolio_id=request.portfolio_id,
        exposure_type=request.exposure_type,
        analysis_date=request.analysis_date
    )
    return exposure


@router.get("/exposures/{portfolio_id}", response_model=List[EquityExposure])
async def get_exposures(portfolio_id: UUID):
    """Get equity exposures for portfolio"""
    exposures = await equity_risk_service.get_exposures(portfolio_id)
    return exposures


@router.post("/scenarios", response_model=EquityScenario)
async def run_scenario(request: ScenarioRequest):
    """Run equity scenario analysis"""
    scenario = await equity_risk_service.run_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        market_shock=request.market_shock,
        sector_shocks=request.sector_shocks
    )
    return scenario


@router.get("/scenarios/{portfolio_id}", response_model=List[EquityScenario])
async def get_scenarios(portfolio_id: UUID):
    """Get equity scenarios for portfolio"""
    scenarios = await equity_risk_service.get_scenarios(portfolio_id)
    return scenarios


@router.get("/sector-breakdown/{portfolio_id}")
async def get_sector_breakdown(portfolio_id: UUID):
    """Get sector breakdown for portfolio"""
    breakdown = await equity_risk_service.get_sector_breakdown(portfolio_id)
    return breakdown


@router.get("/country-breakdown/{portfolio_id}")
async def get_country_breakdown(portfolio_id: UUID):
    """Get country breakdown for portfolio"""
    breakdown = await equity_risk_service.get_country_breakdown(portfolio_id)
    return breakdown


@router.get("/statistics")
async def get_statistics():
    """Get equity risk statistics"""
    return await equity_risk_service.get_statistics()
