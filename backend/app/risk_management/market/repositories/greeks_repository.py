"""Greeks Repository - Data access layer for options greeks"""

from typing import Any
from uuid import UUID

from ..models.greeks_models import GreeksCalculation, GreeksLimit, GreeksSensitivity, OptionPosition, PortfolioGreeks


class GreeksRepository:
    def __init__(self):
        self._positions: dict[UUID, OptionPosition] = {}
        self._calculations: dict[UUID, GreeksCalculation] = {}
        self._portfolio_greeks: dict[UUID, PortfolioGreeks] = {}
        self._limits: dict[UUID, GreeksLimit] = {}
        self._sensitivities: dict[UUID, GreeksSensitivity] = {}

    async def save_position(self, position: OptionPosition) -> OptionPosition:
        self._positions[position.position_id] = position
        return position

    async def find_position_by_id(self, pos_id: UUID) -> OptionPosition | None:
        return self._positions.get(pos_id)

    async def find_positions_by_portfolio(self, portfolio_id: UUID) -> list[OptionPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def find_positions_by_underlying(self, underlying: str) -> list[OptionPosition]:
        return [p for p in self._positions.values() if p.underlying == underlying]

    async def save_calculation(self, calc: GreeksCalculation) -> GreeksCalculation:
        self._calculations[calc.calculation_id] = calc
        return calc

    async def find_calculations_by_position(self, position_id: UUID) -> list[GreeksCalculation]:
        return [c for c in self._calculations.values() if c.position_id == position_id]

    async def save_portfolio_greeks(self, greeks: PortfolioGreeks) -> PortfolioGreeks:
        self._portfolio_greeks[greeks.portfolio_id] = greeks
        return greeks

    async def find_portfolio_greeks(self, portfolio_id: UUID) -> PortfolioGreeks | None:
        return self._portfolio_greeks.get(portfolio_id)

    async def save_limit(self, limit: GreeksLimit) -> GreeksLimit:
        self._limits[limit.limit_id] = limit
        return limit

    async def save_sensitivity(self, sensitivity: GreeksSensitivity) -> GreeksSensitivity:
        self._sensitivities[sensitivity.sensitivity_id] = sensitivity
        return sensitivity

    async def get_statistics(self) -> dict[str, Any]:
        return {"total_positions": len(self._positions), "total_calculations": len(self._calculations)}


greeks_repository = GreeksRepository()
