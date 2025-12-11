"""Greeks Routes - API endpoints for options greeks management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.greeks_models import (
    OptionPosition, GreeksCalculation, PortfolioGreeks, GreeksLimit,
    GreeksSensitivity, OptionType, OptionStyle, ExerciseType
)
from ..services.greeks_service import greeks_service

router = APIRouter(prefix="/greeks", tags=["Options Greeks"])


class OptionPositionRequest(BaseModel):
    portfolio_id: UUID
    underlying: str
    option_type: OptionType
    option_style: OptionStyle
    strike: Decimal
    expiry_date: date
    quantity: Decimal
    premium: Decimal
    exercise_type: ExerciseType


class GreeksCalculationRequest(BaseModel):
    position_id: UUID
    spot_price: Decimal
    volatility: Decimal
    risk_free_rate: Decimal
    dividend_yield: Optional[Decimal] = Decimal("0")


class PortfolioGreeksRequest(BaseModel):
    portfolio_id: UUID
    calculation_date: date


class GreeksLimitRequest(BaseModel):
    portfolio_id: UUID
    greek_type: str
    limit_value: Decimal
    warning_threshold: Decimal


class SensitivityRequest(BaseModel):
    portfolio_id: UUID
    greek_type: str
    shock_range: List[Decimal]


@router.post("/positions", response_model=OptionPosition)
async def create_position(request: OptionPositionRequest):
    """Create option position"""
    position = await greeks_service.create_position(
        portfolio_id=request.portfolio_id,
        underlying=request.underlying,
        option_type=request.option_type,
        option_style=request.option_style,
        strike=request.strike,
        expiry_date=request.expiry_date,
        quantity=request.quantity,
        premium=request.premium,
        exercise_type=request.exercise_type
    )
    return position


@router.get("/positions/{position_id}", response_model=OptionPosition)
async def get_position(position_id: UUID):
    """Get option position by ID"""
    position = await greeks_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/positions", response_model=List[OptionPosition])
async def list_positions(
    portfolio_id: Optional[UUID] = Query(None),
    underlying: Optional[str] = Query(None),
    option_type: Optional[OptionType] = Query(None)
):
    """List option positions"""
    positions = await greeks_service.list_positions(
        portfolio_id, underlying, option_type
    )
    return positions


@router.delete("/positions/{position_id}")
async def close_position(position_id: UUID):
    """Close option position"""
    success = await greeks_service.close_position(position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"status": "closed"}


@router.post("/calculate", response_model=GreeksCalculation)
async def calculate_greeks(request: GreeksCalculationRequest):
    """Calculate greeks for position"""
    calculation = await greeks_service.calculate_greeks(
        position_id=request.position_id,
        spot_price=request.spot_price,
        volatility=request.volatility,
        risk_free_rate=request.risk_free_rate,
        dividend_yield=request.dividend_yield
    )
    return calculation


@router.get("/calculations/{position_id}", response_model=List[GreeksCalculation])
async def get_calculations(position_id: UUID):
    """Get greeks calculations for position"""
    calculations = await greeks_service.get_calculations(position_id)
    return calculations


@router.get("/calculations/{position_id}/latest", response_model=GreeksCalculation)
async def get_latest_calculation(position_id: UUID):
    """Get latest greeks calculation for position"""
    calculation = await greeks_service.get_latest_calculation(position_id)
    if not calculation:
        raise HTTPException(status_code=404, detail="No calculations found")
    return calculation


@router.post("/portfolio", response_model=PortfolioGreeks)
async def calculate_portfolio_greeks(request: PortfolioGreeksRequest):
    """Calculate aggregated portfolio greeks"""
    greeks = await greeks_service.calculate_portfolio_greeks(
        portfolio_id=request.portfolio_id,
        calculation_date=request.calculation_date
    )
    return greeks


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioGreeks)
async def get_portfolio_greeks(portfolio_id: UUID):
    """Get portfolio greeks"""
    greeks = await greeks_service.get_portfolio_greeks(portfolio_id)
    if not greeks:
        raise HTTPException(status_code=404, detail="Portfolio greeks not found")
    return greeks


@router.post("/limits", response_model=GreeksLimit)
async def create_limit(request: GreeksLimitRequest):
    """Create greeks limit"""
    limit = await greeks_service.create_limit(
        portfolio_id=request.portfolio_id,
        greek_type=request.greek_type,
        limit_value=request.limit_value,
        warning_threshold=request.warning_threshold
    )
    return limit


@router.get("/limits/{portfolio_id}", response_model=List[GreeksLimit])
async def get_limits(portfolio_id: UUID):
    """Get greeks limits for portfolio"""
    limits = await greeks_service.get_limits(portfolio_id)
    return limits


@router.post("/limits/check/{portfolio_id}")
async def check_limit_breaches(portfolio_id: UUID):
    """Check greeks limit breaches"""
    breaches = await greeks_service.check_limit_breaches(portfolio_id)
    return breaches


@router.post("/sensitivity", response_model=GreeksSensitivity)
async def run_sensitivity(request: SensitivityRequest):
    """Run greeks sensitivity analysis"""
    sensitivity = await greeks_service.run_sensitivity_analysis(
        portfolio_id=request.portfolio_id,
        greek_type=request.greek_type,
        shock_range=request.shock_range
    )
    return sensitivity


@router.get("/sensitivity/{portfolio_id}", response_model=List[GreeksSensitivity])
async def get_sensitivities(portfolio_id: UUID):
    """Get sensitivity analyses for portfolio"""
    sensitivities = await greeks_service.get_sensitivities(portfolio_id)
    return sensitivities


@router.get("/expiry-profile/{portfolio_id}")
async def get_expiry_profile(portfolio_id: UUID):
    """Get option expiry profile for portfolio"""
    profile = await greeks_service.get_expiry_profile(portfolio_id)
    return profile


@router.get("/underlying-breakdown/{portfolio_id}")
async def get_underlying_breakdown(portfolio_id: UUID):
    """Get greeks breakdown by underlying"""
    breakdown = await greeks_service.get_underlying_breakdown(portfolio_id)
    return breakdown


@router.get("/statistics")
async def get_statistics():
    """Get greeks service statistics"""
    return await greeks_service.get_statistics()
