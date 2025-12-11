"""Greeks Repository - Data access layer for options greeks"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.greeks_models import OptionPosition, GreeksCalculation, PortfolioGreeks, GreeksLimit, GreeksSensitivity


class GreeksRepository:
    def __init__(self):
        self._positions: Dict[UUID, OptionPosition] = {}
        self._calculations: Dict[UUID, GreeksCalculation] = {}
        self._portfolio_greeks: Dict[UUID, PortfolioGreeks] = {}
        self._limits: Dict[UUID, GreeksLimit] = {}
        self._sensitivities: Dict[UUID, GreeksSensitivity] = {}

    async def save_position(self, position: OptionPosition) -> OptionPosition:
        self._positions[position.position_id] = position
        return position

    async def find_position_by_id(self, pos_id: UUID) -> Optional[OptionPosition]:
        return self._positions.get(pos_id)

    async def find_positions_by_portfolio(self, portfolio_id: UUID) -> List[OptionPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def find_positions_by_underlying(self, underlying: str) -> List[OptionPosition]:
        return [p for p in self._positions.values() if p.underlying == underlying]

    async def save_calculation(self, calc: GreeksCalculation) -> GreeksCalculation:
        self._calculations[calc.calculation_id] = calc
        return calc

    async def find_calculations_by_position(self, position_id: UUID) -> List[GreeksCalculation]:
        return [c for c in self._calculations.values() if c.position_id == position_id]

    async def save_portfolio_greeks(self, greeks: PortfolioGreeks) -> PortfolioGreeks:
        self._portfolio_greeks[greeks.portfolio_id] = greeks
        return greeks

    async def find_portfolio_greeks(self, portfolio_id: UUID) -> Optional[PortfolioGreeks]:
        return self._portfolio_greeks.get(portfolio_id)

    async def save_limit(self, limit: GreeksLimit) -> GreeksLimit:
        self._limits[limit.limit_id] = limit
        return limit

    async def save_sensitivity(self, sensitivity: GreeksSensitivity) -> GreeksSensitivity:
        self._sensitivities[sensitivity.sensitivity_id] = sensitivity
        return sensitivity

    async def get_statistics(self) -> Dict[str, Any]:
        return {"total_positions": len(self._positions), "total_calculations": len(self._calculations)}


greeks_repository = GreeksRepository()
