"""FX Risk Repository - Data access layer for FX risk"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.fx_risk_models import FXPosition, FXExposure, FXRate, FXVolatilitySurface, FXScenario


class FXRiskRepository:
    def __init__(self):
        self._positions: Dict[UUID, FXPosition] = {}
        self._exposures: Dict[UUID, FXExposure] = {}
        self._rates: Dict[UUID, FXRate] = {}
        self._vol_surfaces: Dict[UUID, FXVolatilitySurface] = {}
        self._scenarios: Dict[UUID, FXScenario] = {}

    async def save_position(self, position: FXPosition) -> FXPosition:
        self._positions[position.position_id] = position
        return position

    async def find_position_by_id(self, pos_id: UUID) -> Optional[FXPosition]:
        return self._positions.get(pos_id)

    async def find_positions_by_portfolio(self, portfolio_id: UUID) -> List[FXPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def find_positions_by_currency(self, currency: str) -> List[FXPosition]:
        return [p for p in self._positions.values() if p.base_currency == currency]

    async def save_exposure(self, exposure: FXExposure) -> FXExposure:
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def save_rate(self, rate: FXRate) -> FXRate:
        self._rates[rate.rate_id] = rate
        return rate

    async def find_rate_by_pair(self, currency_pair: str) -> Optional[FXRate]:
        for rate in sorted(self._rates.values(), key=lambda x: x.rate_time, reverse=True):
            if rate.currency_pair == currency_pair:
                return rate
        return None

    async def save_vol_surface(self, surface: FXVolatilitySurface) -> FXVolatilitySurface:
        self._vol_surfaces[surface.surface_id] = surface
        return surface

    async def save_scenario(self, scenario: FXScenario) -> FXScenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_statistics(self) -> Dict[str, Any]:
        return {"total_positions": len(self._positions), "total_exposures": len(self._exposures)}


fx_risk_repository = FXRiskRepository()
