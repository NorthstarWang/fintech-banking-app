"""Commodity Routes - API endpoints for commodity risk management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.commodity_models import (
    CommodityPosition, CommodityCurve, CommodityExposure, CommodityScenario,
    CommodityType, CommodityUnit, DeliveryMonth
)
from ..services.commodity_service import commodity_service

router = APIRouter(prefix="/commodity-risk", tags=["Commodity Risk"])


class CommodityPositionRequest(BaseModel):
    portfolio_id: UUID
    commodity_type: CommodityType
    commodity_name: str
    quantity: Decimal
    unit: CommodityUnit
    price: Decimal
    delivery_month: DeliveryMonth
    delivery_year: int


class CommodityCurveRequest(BaseModel):
    commodity_name: str
    commodity_type: CommodityType
    tenors: List[str]
    prices: List[Decimal]
    curve_date: date


class ExposureRequest(BaseModel):
    portfolio_id: UUID
    commodity_type: CommodityType
    exposure_date: date


class ScenarioRequest(BaseModel):
    portfolio_id: UUID
    scenario_name: str
    price_shocks: dict
    volatility_shocks: Optional[dict] = None


@router.post("/positions", response_model=CommodityPosition)
async def create_position(request: CommodityPositionRequest):
    """Create commodity position"""
    position = await commodity_service.create_position(
        portfolio_id=request.portfolio_id,
        commodity_type=request.commodity_type,
        commodity_name=request.commodity_name,
        quantity=request.quantity,
        unit=request.unit,
        price=request.price,
        delivery_month=request.delivery_month,
        delivery_year=request.delivery_year
    )
    return position


@router.get("/positions/{position_id}", response_model=CommodityPosition)
async def get_position(position_id: UUID):
    """Get commodity position by ID"""
    position = await commodity_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/positions", response_model=List[CommodityPosition])
async def list_positions(
    portfolio_id: Optional[UUID] = Query(None),
    commodity_type: Optional[CommodityType] = Query(None),
    commodity_name: Optional[str] = Query(None)
):
    """List commodity positions"""
    positions = await commodity_service.list_positions(
        portfolio_id, commodity_type, commodity_name
    )
    return positions


@router.put("/positions/{position_id}/price", response_model=CommodityPosition)
async def update_position_price(position_id: UUID, price: Decimal):
    """Update commodity position price"""
    position = await commodity_service.update_position_price(position_id, price)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.delete("/positions/{position_id}")
async def close_position(position_id: UUID):
    """Close commodity position"""
    success = await commodity_service.close_position(position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"status": "closed"}


@router.post("/curves", response_model=CommodityCurve)
async def create_curve(request: CommodityCurveRequest):
    """Create commodity forward curve"""
    curve = await commodity_service.create_curve(
        commodity_name=request.commodity_name,
        commodity_type=request.commodity_type,
        tenors=request.tenors,
        prices=request.prices,
        curve_date=request.curve_date
    )
    return curve


@router.get("/curves/{commodity_name}", response_model=CommodityCurve)
async def get_curve(commodity_name: str):
    """Get latest commodity curve"""
    curve = await commodity_service.get_curve(commodity_name)
    if not curve:
        raise HTTPException(status_code=404, detail="Curve not found")
    return curve


@router.get("/curves", response_model=List[CommodityCurve])
async def list_curves(commodity_type: Optional[CommodityType] = Query(None)):
    """List commodity curves"""
    curves = await commodity_service.list_curves(commodity_type)
    return curves


@router.post("/exposures", response_model=CommodityExposure)
async def calculate_exposure(request: ExposureRequest):
    """Calculate commodity exposure"""
    exposure = await commodity_service.calculate_exposure(
        portfolio_id=request.portfolio_id,
        commodity_type=request.commodity_type,
        exposure_date=request.exposure_date
    )
    return exposure


@router.get("/exposures/{portfolio_id}", response_model=List[CommodityExposure])
async def get_exposures(portfolio_id: UUID):
    """Get commodity exposures for portfolio"""
    exposures = await commodity_service.get_exposures(portfolio_id)
    return exposures


@router.get("/exposures/{portfolio_id}/by-type")
async def get_exposures_by_type(portfolio_id: UUID):
    """Get commodity exposures grouped by type"""
    exposures = await commodity_service.get_exposures_by_type(portfolio_id)
    return exposures


@router.post("/scenarios", response_model=CommodityScenario)
async def run_scenario(request: ScenarioRequest):
    """Run commodity scenario analysis"""
    scenario = await commodity_service.run_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        price_shocks=request.price_shocks,
        volatility_shocks=request.volatility_shocks
    )
    return scenario


@router.get("/scenarios/{portfolio_id}", response_model=List[CommodityScenario])
async def get_scenarios(portfolio_id: UUID):
    """Get commodity scenarios for portfolio"""
    scenarios = await commodity_service.get_scenarios(portfolio_id)
    return scenarios


@router.get("/spot-prices")
async def get_spot_prices(commodity_type: Optional[CommodityType] = Query(None)):
    """Get current spot prices"""
    prices = await commodity_service.get_spot_prices(commodity_type)
    return prices


@router.get("/delivery-schedule/{portfolio_id}")
async def get_delivery_schedule(portfolio_id: UUID):
    """Get delivery schedule for portfolio"""
    schedule = await commodity_service.get_delivery_schedule(portfolio_id)
    return schedule


@router.get("/statistics")
async def get_statistics():
    """Get commodity risk statistics"""
    return await commodity_service.get_statistics()
