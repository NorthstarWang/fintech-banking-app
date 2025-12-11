"""Position Routes - API endpoints for trading position management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.position_models import (
    TradingPosition, DailyPnL, PnLAttribution, PortfolioValuation,
    TradingBook, AssetClass, PositionStatus, PositionDirection
)
from ..services.position_service import position_service

router = APIRouter(prefix="/positions", tags=["Trading Positions"])


class PositionRequest(BaseModel):
    portfolio_id: UUID
    book_id: str
    instrument_id: str
    instrument_name: str
    asset_class: AssetClass
    direction: PositionDirection
    quantity: Decimal
    entry_price: Decimal
    currency: str


class PositionUpdateRequest(BaseModel):
    quantity: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    status: Optional[PositionStatus] = None


class DailyPnLRequest(BaseModel):
    portfolio_id: UUID
    pnl_date: date
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class PnLAttributionRequest(BaseModel):
    portfolio_id: UUID
    attribution_date: date
    attribution_type: str
    components: dict


class ValuationRequest(BaseModel):
    portfolio_id: UUID
    valuation_date: date


class TradingBookRequest(BaseModel):
    book_code: str
    book_name: str
    book_type: str
    trader_id: str
    desk_id: str


@router.post("/", response_model=TradingPosition)
async def create_position(request: PositionRequest):
    """Create trading position"""
    position = await position_service.create_position(
        portfolio_id=request.portfolio_id,
        book_id=request.book_id,
        instrument_id=request.instrument_id,
        instrument_name=request.instrument_name,
        asset_class=request.asset_class,
        direction=request.direction,
        quantity=request.quantity,
        entry_price=request.entry_price,
        currency=request.currency
    )
    return position


@router.get("/{position_id}", response_model=TradingPosition)
async def get_position(position_id: UUID):
    """Get trading position by ID"""
    position = await position_service.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.get("/", response_model=List[TradingPosition])
async def list_positions(
    portfolio_id: Optional[UUID] = Query(None),
    book_id: Optional[str] = Query(None),
    asset_class: Optional[AssetClass] = Query(None),
    status: Optional[PositionStatus] = Query(None)
):
    """List trading positions"""
    positions = await position_service.list_positions(
        portfolio_id, book_id, asset_class, status
    )
    return positions


@router.put("/{position_id}", response_model=TradingPosition)
async def update_position(position_id: UUID, request: PositionUpdateRequest):
    """Update trading position"""
    position = await position_service.update_position(
        position_id=position_id,
        quantity=request.quantity,
        current_price=request.current_price,
        status=request.status
    )
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/{position_id}/close", response_model=TradingPosition)
async def close_position(position_id: UUID, close_price: Decimal):
    """Close trading position"""
    position = await position_service.close_position(position_id, close_price)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/pnl/daily", response_model=DailyPnL)
async def record_daily_pnl(request: DailyPnLRequest):
    """Record daily P&L"""
    pnl = await position_service.record_daily_pnl(
        portfolio_id=request.portfolio_id,
        pnl_date=request.pnl_date,
        realized_pnl=request.realized_pnl,
        unrealized_pnl=request.unrealized_pnl
    )
    return pnl


@router.get("/pnl/daily/{portfolio_id}", response_model=List[DailyPnL])
async def get_daily_pnl(
    portfolio_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get daily P&L history"""
    pnl = await position_service.get_daily_pnl(portfolio_id, start_date, end_date)
    return pnl


@router.get("/pnl/daily/{portfolio_id}/date/{pnl_date}", response_model=DailyPnL)
async def get_pnl_by_date(portfolio_id: UUID, pnl_date: date):
    """Get P&L for specific date"""
    pnl = await position_service.get_pnl_by_date(portfolio_id, pnl_date)
    if not pnl:
        raise HTTPException(status_code=404, detail="P&L not found")
    return pnl


@router.post("/pnl/attribution", response_model=PnLAttribution)
async def create_attribution(request: PnLAttributionRequest):
    """Create P&L attribution"""
    attribution = await position_service.create_attribution(
        portfolio_id=request.portfolio_id,
        attribution_date=request.attribution_date,
        attribution_type=request.attribution_type,
        components=request.components
    )
    return attribution


@router.get("/pnl/attribution/{portfolio_id}", response_model=List[PnLAttribution])
async def get_attributions(portfolio_id: UUID):
    """Get P&L attributions for portfolio"""
    attributions = await position_service.get_attributions(portfolio_id)
    return attributions


@router.post("/valuation", response_model=PortfolioValuation)
async def create_valuation(request: ValuationRequest):
    """Create portfolio valuation"""
    valuation = await position_service.create_valuation(
        portfolio_id=request.portfolio_id,
        valuation_date=request.valuation_date
    )
    return valuation


@router.get("/valuation/{portfolio_id}", response_model=PortfolioValuation)
async def get_valuation(portfolio_id: UUID):
    """Get latest portfolio valuation"""
    valuation = await position_service.get_latest_valuation(portfolio_id)
    if not valuation:
        raise HTTPException(status_code=404, detail="Valuation not found")
    return valuation


@router.get("/valuation/{portfolio_id}/history", response_model=List[PortfolioValuation])
async def get_valuation_history(portfolio_id: UUID):
    """Get portfolio valuation history"""
    valuations = await position_service.get_valuation_history(portfolio_id)
    return valuations


@router.post("/books", response_model=TradingBook)
async def create_book(request: TradingBookRequest):
    """Create trading book"""
    book = await position_service.create_book(
        book_code=request.book_code,
        book_name=request.book_name,
        book_type=request.book_type,
        trader_id=request.trader_id,
        desk_id=request.desk_id
    )
    return book


@router.get("/books/{book_code}", response_model=TradingBook)
async def get_book(book_code: str):
    """Get trading book by code"""
    book = await position_service.get_book(book_code)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/books", response_model=List[TradingBook])
async def list_books():
    """List all trading books"""
    books = await position_service.list_books()
    return books


@router.get("/asset-class-summary/{portfolio_id}")
async def get_asset_class_summary(portfolio_id: UUID):
    """Get position summary by asset class"""
    summary = await position_service.get_asset_class_summary(portfolio_id)
    return summary


@router.get("/book-summary/{book_id}")
async def get_book_summary(book_id: str):
    """Get position summary for trading book"""
    summary = await position_service.get_book_summary(book_id)
    return summary


@router.get("/statistics")
async def get_statistics():
    """Get position service statistics"""
    return await position_service.get_statistics()
