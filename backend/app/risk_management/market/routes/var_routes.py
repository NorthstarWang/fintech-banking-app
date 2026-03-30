"""VaR Routes - API endpoints for Value at Risk calculations"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.var_models import VaRBacktest, VaRCalculation, VaRException, VaRLimit, VaRMethodology
from ..services.var_service import var_service

router = APIRouter(prefix="/var", tags=["Value at Risk"])


class VaRCalculationRequest(BaseModel):
    portfolio_id: UUID
    methodology: VaRMethodology
    confidence_level: Decimal
    time_horizon: int
    historical_window: int | None = 250


class VaRLimitRequest(BaseModel):
    portfolio_id: UUID
    limit_type: str
    limit_value: Decimal
    warning_threshold: Decimal


class BacktestRequest(BaseModel):
    portfolio_id: UUID
    calculation_id: UUID
    start_date: date
    end_date: date


@router.post("/calculate", response_model=VaRCalculation)
async def calculate_var(request: VaRCalculationRequest):
    """Calculate Value at Risk for a portfolio"""
    return await var_service.calculate_var(
        portfolio_id=request.portfolio_id,
        methodology=request.methodology,
        confidence_level=request.confidence_level,
        time_horizon=request.time_horizon,
        historical_window=request.historical_window
    )


@router.get("/calculations/{portfolio_id}", response_model=list[VaRCalculation])
async def get_portfolio_var(portfolio_id: UUID):
    """Get VaR calculations for a portfolio"""
    return await var_service.get_portfolio_var_calculations(portfolio_id)


@router.get("/calculation/{calculation_id}", response_model=VaRCalculation)
async def get_calculation(calculation_id: UUID):
    """Get specific VaR calculation"""
    calculation = await var_service.get_var_calculation(calculation_id)
    if not calculation:
        raise HTTPException(status_code=404, detail="VaR calculation not found")
    return calculation


@router.post("/backtest", response_model=VaRBacktest)
async def run_backtest(request: BacktestRequest):
    """Run backtesting on VaR calculation"""
    return await var_service.run_backtest(
        portfolio_id=request.portfolio_id,
        calculation_id=request.calculation_id,
        start_date=request.start_date,
        end_date=request.end_date
    )


@router.get("/backtests/{portfolio_id}", response_model=list[VaRBacktest])
async def get_backtests(portfolio_id: UUID):
    """Get backtest results for portfolio"""
    return await var_service.get_backtest_results(portfolio_id)


@router.post("/limits", response_model=VaRLimit)
async def create_limit(request: VaRLimitRequest):
    """Create VaR limit"""
    return await var_service.create_var_limit(
        portfolio_id=request.portfolio_id,
        limit_type=request.limit_type,
        limit_value=request.limit_value,
        warning_threshold=request.warning_threshold
    )


@router.get("/limits/{portfolio_id}", response_model=list[VaRLimit])
async def get_limits(portfolio_id: UUID):
    """Get VaR limits for portfolio"""
    return await var_service.get_portfolio_limits(portfolio_id)


@router.post("/check-breach/{portfolio_id}")
async def check_limit_breach(portfolio_id: UUID):
    """Check if current VaR breaches limits"""
    return await var_service.check_limit_breach(portfolio_id)


@router.get("/exceptions", response_model=list[VaRException])
async def get_exceptions(
    portfolio_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None)
):
    """Get VaR exceptions"""
    return await var_service.get_exceptions(portfolio_id, start_date, end_date)


@router.get("/statistics")
async def get_statistics():
    """Get VaR service statistics"""
    return await var_service.get_statistics()
