"""VaR Routes - API endpoints for Value at Risk calculations"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.var_models import VaRCalculation, VaRBacktest, VaRLimit, VaRException, VaRMethodology
from ..services.var_service import var_service

router = APIRouter(prefix="/var", tags=["Value at Risk"])


class VaRCalculationRequest(BaseModel):
    portfolio_id: UUID
    methodology: VaRMethodology
    confidence_level: Decimal
    time_horizon: int
    historical_window: Optional[int] = 250


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
    result = await var_service.calculate_var(
        portfolio_id=request.portfolio_id,
        methodology=request.methodology,
        confidence_level=request.confidence_level,
        time_horizon=request.time_horizon,
        historical_window=request.historical_window
    )
    return result


@router.get("/calculations/{portfolio_id}", response_model=List[VaRCalculation])
async def get_portfolio_var(portfolio_id: UUID):
    """Get VaR calculations for a portfolio"""
    calculations = await var_service.get_portfolio_var_calculations(portfolio_id)
    return calculations


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
    result = await var_service.run_backtest(
        portfolio_id=request.portfolio_id,
        calculation_id=request.calculation_id,
        start_date=request.start_date,
        end_date=request.end_date
    )
    return result


@router.get("/backtests/{portfolio_id}", response_model=List[VaRBacktest])
async def get_backtests(portfolio_id: UUID):
    """Get backtest results for portfolio"""
    results = await var_service.get_backtest_results(portfolio_id)
    return results


@router.post("/limits", response_model=VaRLimit)
async def create_limit(request: VaRLimitRequest):
    """Create VaR limit"""
    limit = await var_service.create_var_limit(
        portfolio_id=request.portfolio_id,
        limit_type=request.limit_type,
        limit_value=request.limit_value,
        warning_threshold=request.warning_threshold
    )
    return limit


@router.get("/limits/{portfolio_id}", response_model=List[VaRLimit])
async def get_limits(portfolio_id: UUID):
    """Get VaR limits for portfolio"""
    limits = await var_service.get_portfolio_limits(portfolio_id)
    return limits


@router.post("/check-breach/{portfolio_id}")
async def check_limit_breach(portfolio_id: UUID):
    """Check if current VaR breaches limits"""
    breach_info = await var_service.check_limit_breach(portfolio_id)
    return breach_info


@router.get("/exceptions", response_model=List[VaRException])
async def get_exceptions(
    portfolio_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get VaR exceptions"""
    exceptions = await var_service.get_exceptions(portfolio_id, start_date, end_date)
    return exceptions


@router.get("/statistics")
async def get_statistics():
    """Get VaR service statistics"""
    return await var_service.get_statistics()
