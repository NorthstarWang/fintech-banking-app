"""FX Risk Routes - API endpoints for foreign exchange risk management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.fx_risk_models import (
    FXPosition, FXExposure, FXRate, FXVolatilitySurface, FXScenario,
    FXForward, FXOption, Currency, PositionDirection
)
from ..services.fx_risk_service import fx_risk_service

router = APIRouter(prefix="/fx-risk", tags=["FX Risk"])


class FXPositionRequest(BaseModel):
    portfolio_id: UUID
    base_currency: Currency
    quote_currency: Currency
    notional_amount: Decimal
    direction: PositionDirection
    rate: Decimal
    value_date: date


class FXRateRequest(BaseModel):
    base_currency: Currency
    quote_currency: Currency
    spot_rate: Decimal
    forward_points: Optional[List[Decimal]] = None


class FXExposureRequest(BaseModel):
    portfolio_id: UUID
    currency: Currency
    exposure_date: date


class FXScenarioRequest(BaseModel):
    portfolio_id: UUID
    scenario_name: str
    currency_shocks: dict


class FXForwardRequest(BaseModel):
    portfolio_id: UUID
    base_currency: Currency
    quote_currency: Currency
    notional: Decimal
    forward_rate: Decimal
    settlement_date: date


class FXOptionRequest(BaseModel):
    portfolio_id: UUID
    base_currency: Currency
    quote_currency: Currency
    notional: Decimal
    strike: Decimal
    expiry_date: date
    is_call: bool


@router.post("/positions", response_model=FXPosition)
async def create_position(request: FXPositionRequest):
    """Create FX position"""
    position = await fx_risk_service.create_position(
        portfolio_id=request.portfolio_id,
        base_currency=request.base_currency,
        quote_currency=request.quote_currency,
        notional_amount=request.notional_amount,
        direction=request.direction,
        rate=request.rate,
        value_date=request.value_date
    )
    return position


@router.get("/positions/{position_id}", response_model=FXPosition)
async def get_position(position_id: UUID):
    """Get FX position by ID"""
    position = await fx_risk_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/positions", response_model=List[FXPosition])
async def list_positions(
    portfolio_id: Optional[UUID] = Query(None),
    currency: Optional[Currency] = Query(None)
):
    """List FX positions"""
    positions = await fx_risk_service.list_positions(portfolio_id, currency)
    return positions


@router.post("/rates", response_model=FXRate)
async def update_rate(request: FXRateRequest):
    """Update FX rate"""
    rate = await fx_risk_service.update_rate(
        base_currency=request.base_currency,
        quote_currency=request.quote_currency,
        spot_rate=request.spot_rate,
        forward_points=request.forward_points
    )
    return rate


@router.get("/rates/{base}/{quote}", response_model=FXRate)
async def get_rate(base: Currency, quote: Currency):
    """Get FX rate for currency pair"""
    rate = await fx_risk_service.get_rate(base, quote)
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    return rate


@router.post("/exposures", response_model=FXExposure)
async def calculate_exposure(request: FXExposureRequest):
    """Calculate FX exposure"""
    exposure = await fx_risk_service.calculate_exposure(
        portfolio_id=request.portfolio_id,
        currency=request.currency,
        exposure_date=request.exposure_date
    )
    return exposure


@router.get("/exposures/{portfolio_id}", response_model=List[FXExposure])
async def get_exposures(portfolio_id: UUID):
    """Get FX exposures for portfolio"""
    exposures = await fx_risk_service.get_exposures(portfolio_id)
    return exposures


@router.post("/volatility-surface", response_model=FXVolatilitySurface)
async def create_vol_surface(
    base: Currency,
    quote: Currency,
    tenors: List[str],
    strikes: List[Decimal],
    vols: List[List[Decimal]]
):
    """Create FX volatility surface"""
    surface = await fx_risk_service.create_volatility_surface(
        base, quote, tenors, strikes, vols
    )
    return surface


@router.get("/volatility-surface/{base}/{quote}", response_model=FXVolatilitySurface)
async def get_vol_surface(base: Currency, quote: Currency):
    """Get FX volatility surface"""
    surface = await fx_risk_service.get_volatility_surface(base, quote)
    if not surface:
        raise HTTPException(status_code=404, detail="Volatility surface not found")
    return surface


@router.post("/scenarios", response_model=FXScenario)
async def run_scenario(request: FXScenarioRequest):
    """Run FX scenario analysis"""
    scenario = await fx_risk_service.run_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        currency_shocks=request.currency_shocks
    )
    return scenario


@router.post("/forwards", response_model=FXForward)
async def create_forward(request: FXForwardRequest):
    """Create FX forward"""
    forward = await fx_risk_service.create_forward(
        portfolio_id=request.portfolio_id,
        base_currency=request.base_currency,
        quote_currency=request.quote_currency,
        notional=request.notional,
        forward_rate=request.forward_rate,
        settlement_date=request.settlement_date
    )
    return forward


@router.post("/options", response_model=FXOption)
async def create_option(request: FXOptionRequest):
    """Create FX option"""
    option = await fx_risk_service.create_option(
        portfolio_id=request.portfolio_id,
        base_currency=request.base_currency,
        quote_currency=request.quote_currency,
        notional=request.notional,
        strike=request.strike,
        expiry_date=request.expiry_date,
        is_call=request.is_call
    )
    return option


@router.get("/statistics")
async def get_statistics():
    """Get FX risk statistics"""
    return await fx_risk_service.get_statistics()
