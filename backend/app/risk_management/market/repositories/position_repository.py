"""Position Repository - Data access layer for trading positions"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.position_models import TradingPosition, DailyPnL, PnLAttribution, PortfolioValuation, TradingBook, AssetClass, PositionStatus


class PositionRepository:
    def __init__(self):
        self._positions: Dict[UUID, TradingPosition] = {}
        self._daily_pnl: Dict[UUID, DailyPnL] = {}
        self._attributions: Dict[UUID, PnLAttribution] = {}
        self._valuations: Dict[UUID, PortfolioValuation] = {}
        self._books: Dict[UUID, TradingBook] = {}

    async def save_position(self, position: TradingPosition) -> TradingPosition:
        self._positions[position.position_id] = position
        return position

    async def find_position_by_id(self, pos_id: UUID) -> Optional[TradingPosition]:
        return self._positions.get(pos_id)

    async def find_positions_by_portfolio(self, portfolio_id: UUID) -> List[TradingPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def find_positions_by_asset_class(self, asset_class: AssetClass) -> List[TradingPosition]:
        return [p for p in self._positions.values() if p.asset_class == asset_class]

    async def find_positions_by_status(self, status: PositionStatus) -> List[TradingPosition]:
        return [p for p in self._positions.values() if p.status == status]

    async def find_positions_by_book(self, book_id: str) -> List[TradingPosition]:
        return [p for p in self._positions.values() if p.book_id == book_id]

    async def update_position(self, position: TradingPosition) -> TradingPosition:
        self._positions[position.position_id] = position
        return position

    async def save_daily_pnl(self, pnl: DailyPnL) -> DailyPnL:
        self._daily_pnl[pnl.pnl_id] = pnl
        return pnl

    async def find_pnl_by_portfolio_date(self, portfolio_id: UUID, pnl_date: date) -> Optional[DailyPnL]:
        for pnl in self._daily_pnl.values():
            if pnl.portfolio_id == portfolio_id and pnl.pnl_date == pnl_date:
                return pnl
        return None

    async def save_attribution(self, attribution: PnLAttribution) -> PnLAttribution:
        self._attributions[attribution.attribution_id] = attribution
        return attribution

    async def save_valuation(self, valuation: PortfolioValuation) -> PortfolioValuation:
        self._valuations[valuation.valuation_id] = valuation
        return valuation

    async def find_valuation_by_portfolio(self, portfolio_id: UUID) -> Optional[PortfolioValuation]:
        for val in sorted(self._valuations.values(), key=lambda x: x.valuation_date, reverse=True):
            if val.portfolio_id == portfolio_id:
                return val
        return None

    async def save_book(self, book: TradingBook) -> TradingBook:
        self._books[book.book_id] = book
        return book

    async def find_book_by_code(self, book_code: str) -> Optional[TradingBook]:
        for book in self._books.values():
            if book.book_code == book_code:
                return book
        return None

    async def get_statistics(self) -> Dict[str, Any]:
        total_mv = sum(p.market_value for p in self._positions.values())
        return {"total_positions": len(self._positions), "total_market_value": total_mv}


position_repository = PositionRepository()
