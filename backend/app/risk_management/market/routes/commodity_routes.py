"""Commodity Routes - API endpoints for commodity risk management"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.commodity_models import (
    CommodityCurve,
    CommodityExposure,
    CommodityPosition,
    CommodityScenario,
    CommodityType,
    CommodityUnit,
    DeliveryMonth,
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
    tenors: list[str]
    prices: list[Decimal]
    curve_date: date


class ExposureRequest(BaseModel):
    portfolio_id: UUID
    commodity_type: CommodityType
    exposure_date: date


class ScenarioRequest(BaseModel):
    portfolio_id: UUID
    scenario_name: str
    price_shocks: dict
    volatility_shocks: dict | None = None


@router.post("/positions", response_model=CommodityPosition)
async def create_position(request: CommodityPositionRequest):
    """Create commodity position"""
    return await commodity_service.create_position(
        portfolio_id=request.portfolio_id,
        commodity_type=request.commodity_type,
        commodity_name=request.commodity_name,
        quantity=request.quantity,
        unit=request.unit,
        price=request.price,
        delivery_month=request.delivery_month,
        delivery_year=request.delivery_year
    )


@router.get("/positions/{position_id}", response_model=CommodityPosition)
async def get_position(position_id: UUID):
    """Get commodity position by ID"""
    position = await commodity_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/positions", response_model=list[CommodityPosition])
async def list_positions(
    portfolio_id: UUID | None = Query(None),
    commodity_type: CommodityType | None = Query(None),
    commodity_name: str | None = Query(None)
):
    """List commodity positions"""
    return await commodity_service.list_positions(
        portfolio_id, commodity_type, commodity_name
    )


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
    return await commodity_service.create_curve(
        commodity_name=request.commodity_name,
        commodity_type=request.commodity_type,
        tenors=request.tenors,
        prices=request.prices,
        curve_date=request.curve_date
    )


@router.get("/curves/{commodity_name}", response_model=CommodityCurve)
async def get_curve(commodity_name: str):
    """Get latest commodity curve"""
    curve = await commodity_service.get_curve(commodity_name)
    if not curve:
        raise HTTPException(status_code=404, detail="Curve not found")
    return curve


@router.get("/curves", response_model=list[CommodityCurve])
async def list_curves(commodity_type: CommodityType | None = Query(None)):
    """List commodity curves"""
    return await commodity_service.list_curves(commodity_type)


@router.post("/exposures", response_model=CommodityExposure)
async def calculate_exposure(request: ExposureRequest):
    """Calculate commodity exposure"""
    return await commodity_service.calculate_exposure(
        portfolio_id=request.portfolio_id,
        commodity_type=request.commodity_type,
        exposure_date=request.exposure_date
    )


@router.get("/exposures/{portfolio_id}", response_model=list[CommodityExposure])
async def get_exposures(portfolio_id: UUID):
    """Get commodity exposures for portfolio"""
    return await commodity_service.get_exposures(portfolio_id)


@router.get("/exposures/{portfolio_id}/by-type")
async def get_exposures_by_type(portfolio_id: UUID):
    """Get commodity exposures grouped by type"""
    return await commodity_service.get_exposures_by_type(portfolio_id)


@router.post("/scenarios", response_model=CommodityScenario)
async def run_scenario(request: ScenarioRequest):
    """Run commodity scenario analysis"""
    return await commodity_service.run_scenario(
        portfolio_id=request.portfolio_id,
        scenario_name=request.scenario_name,
        price_shocks=request.price_shocks,
        volatility_shocks=request.volatility_shocks
    )


@router.get("/scenarios/{portfolio_id}", response_model=list[CommodityScenario])
async def get_scenarios(portfolio_id: UUID):
    """Get commodity scenarios for portfolio"""
    return await commodity_service.get_scenarios(portfolio_id)


@router.get("/spot-prices")
async def get_spot_prices(commodity_type: CommodityType | None = Query(None)):
    """Get current spot prices"""
    return await commodity_service.get_spot_prices(commodity_type)


@router.get("/delivery-schedule/{portfolio_id}")
async def get_delivery_schedule(portfolio_id: UUID):
    """Get delivery schedule for portfolio"""
    return await commodity_service.get_delivery_schedule(portfolio_id)


@router.get("/statistics")
async def get_statistics():
    """Get commodity risk statistics"""
    return await commodity_service.get_statistics()
