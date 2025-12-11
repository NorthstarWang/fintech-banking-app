"""Position Service - Trading position and P&L management service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.position_models import (
    TradingPosition, DailyPnL, PnLAttribution, PortfolioValuation,
    TradingBook, PositionStatistics, AssetClass, PositionStatus
)


class PositionService:
    def __init__(self):
        self._positions: Dict[UUID, TradingPosition] = {}
        self._daily_pnl: Dict[UUID, DailyPnL] = {}
        self._attributions: Dict[UUID, PnLAttribution] = {}
        self._valuations: Dict[UUID, PortfolioValuation] = {}
        self._books: Dict[UUID, TradingBook] = {}
        self._counter = 0

    def _generate_reference(self) -> str:
        self._counter += 1
        return f"POS-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    async def create_position(
        self, asset_class: AssetClass, instrument_id: str, instrument_name: str,
        portfolio_id: UUID, book_id: str, trader_id: str, quantity: float,
        direction: str, entry_price: float, current_price: float, currency: str
    ) -> TradingPosition:
        market_value = abs(quantity) * current_price
        cost_basis = abs(quantity) * entry_price
        unrealized_pnl = (current_price - entry_price) * quantity
        if direction == "short":
            unrealized_pnl = -unrealized_pnl

        position = TradingPosition(
            position_reference=self._generate_reference(),
            asset_class=asset_class,
            instrument_id=instrument_id,
            instrument_name=instrument_name,
            portfolio_id=portfolio_id,
            book_id=book_id,
            trader_id=trader_id,
            quantity=quantity,
            direction=direction,
            entry_date=date.today(),
            entry_price=entry_price,
            current_price=current_price,
            market_value=market_value,
            cost_basis=cost_basis,
            unrealized_pnl=unrealized_pnl,
            total_pnl=unrealized_pnl,
            currency=currency
        )
        self._positions[position.position_id] = position
        return position

    async def get_position(self, position_id: UUID) -> Optional[TradingPosition]:
        return self._positions.get(position_id)

    async def update_price(self, position_id: UUID, new_price: float) -> Optional[TradingPosition]:
        position = self._positions.get(position_id)
        if position:
            old_pnl = position.unrealized_pnl
            position.current_price = new_price
            position.market_value = abs(position.quantity) * new_price
            position.unrealized_pnl = (new_price - position.entry_price) * position.quantity
            if position.direction == "short":
                position.unrealized_pnl = -position.unrealized_pnl
            position.total_pnl = position.unrealized_pnl + position.realized_pnl
            position.updated_at = datetime.utcnow()
        return position

    async def close_position(self, position_id: UUID, close_price: float) -> Optional[TradingPosition]:
        position = self._positions.get(position_id)
        if position:
            realized = (close_price - position.entry_price) * position.quantity
            if position.direction == "short":
                realized = -realized
            position.realized_pnl = realized
            position.unrealized_pnl = 0
            position.total_pnl = realized
            position.status = PositionStatus.CLOSED
            position.current_price = close_price
            position.updated_at = datetime.utcnow()
        return position

    async def calculate_daily_pnl(
        self, portfolio_id: UUID, opening_value: float, closing_value: float, net_flows: float = 0
    ) -> DailyPnL:
        total_pnl = closing_value - opening_value - net_flows

        # Simplified P&L breakdown
        trading_pnl = total_pnl * 0.7
        carry_pnl = total_pnl * 0.15
        fx_pnl = total_pnl * 0.1
        other_pnl = total_pnl * 0.05

        daily_pnl = DailyPnL(
            portfolio_id=portfolio_id,
            pnl_date=date.today(),
            opening_value=opening_value,
            closing_value=closing_value,
            net_flows=net_flows,
            total_pnl=total_pnl,
            trading_pnl=trading_pnl,
            carry_pnl=carry_pnl,
            fx_pnl=fx_pnl,
            other_pnl=other_pnl,
            mtm_pnl=trading_pnl
        )
        self._daily_pnl[daily_pnl.pnl_id] = daily_pnl
        return daily_pnl

    async def calculate_pnl_attribution(self, portfolio_id: UUID, total_pnl: float) -> PnLAttribution:
        # Simplified attribution
        attribution = PnLAttribution(
            portfolio_id=portfolio_id,
            attribution_date=date.today(),
            total_pnl=total_pnl,
            market_pnl=total_pnl * 0.5,
            delta_pnl=total_pnl * 0.3,
            gamma_pnl=total_pnl * 0.05,
            vega_pnl=total_pnl * 0.05,
            theta_pnl=total_pnl * 0.03,
            rho_pnl=total_pnl * 0.02,
            fx_translation_pnl=total_pnl * 0.02,
            carry_pnl=total_pnl * 0.02,
            trade_pnl=total_pnl * 0.01,
            unexplained_pnl=0
        )
        self._attributions[attribution.attribution_id] = attribution
        return attribution

    async def calculate_portfolio_valuation(self, portfolio_id: UUID) -> PortfolioValuation:
        positions = [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

        total_mv = sum(p.market_value for p in positions)
        total_cost = sum(p.cost_basis for p in positions)
        total_unrealized = sum(p.unrealized_pnl for p in positions)
        total_realized = sum(p.realized_pnl for p in positions)

        by_asset_class = {}
        by_currency = {}
        for pos in positions:
            by_asset_class[pos.asset_class.value] = by_asset_class.get(pos.asset_class.value, 0) + pos.market_value
            by_currency[pos.currency] = by_currency.get(pos.currency, 0) + pos.market_value

        valuation = PortfolioValuation(
            portfolio_id=portfolio_id,
            valuation_date=date.today(),
            total_market_value=total_mv,
            total_cost_basis=total_cost,
            total_unrealized_pnl=total_unrealized,
            total_realized_pnl=total_realized,
            cash_balance=0,
            collateral_value=0,
            net_asset_value=total_mv,
            by_asset_class=by_asset_class,
            by_currency=by_currency
        )
        self._valuations[valuation.valuation_id] = valuation
        return valuation

    async def create_book(
        self, book_code: str, book_name: str, book_type: str,
        trader_id: str, desk: str, entity: str, base_currency: str,
        var_limit: float, pnl_limit: float
    ) -> TradingBook:
        book = TradingBook(
            book_code=book_code,
            book_name=book_name,
            book_type=book_type,
            trader_id=trader_id,
            desk=desk,
            entity=entity,
            base_currency=base_currency,
            var_limit=var_limit,
            pnl_limit=pnl_limit,
            gross_limit=var_limit * 10,
            net_limit=var_limit * 5
        )
        self._books[book.book_id] = book
        return book

    async def get_portfolio_positions(self, portfolio_id: UUID) -> List[TradingPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def get_statistics(self) -> PositionStatistics:
        stats = PositionStatistics(
            total_positions=len(self._positions),
            total_market_value=sum(p.market_value for p in self._positions.values()),
            total_unrealized_pnl=sum(p.unrealized_pnl for p in self._positions.values()),
            total_realized_pnl=sum(p.realized_pnl for p in self._positions.values())
        )
        for pos in self._positions.values():
            stats.by_asset_class[pos.asset_class.value] = stats.by_asset_class.get(pos.asset_class.value, 0) + 1
            stats.by_status[pos.status.value] = stats.by_status.get(pos.status.value, 0) + 1
        return stats


position_service = PositionService()
