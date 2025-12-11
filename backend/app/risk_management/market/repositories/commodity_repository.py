"""Commodity Repository - Data access layer for commodity risk"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.commodity_models import CommodityPosition, CommodityCurve, CommodityExposure, CommodityScenario, CommodityType


class CommodityRepository:
    def __init__(self):
        self._positions: Dict[UUID, CommodityPosition] = {}
        self._curves: Dict[UUID, CommodityCurve] = {}
        self._exposures: Dict[UUID, CommodityExposure] = {}
        self._scenarios: Dict[UUID, CommodityScenario] = {}

    async def save_position(self, position: CommodityPosition) -> CommodityPosition:
        self._positions[position.position_id] = position
        return position

    async def find_position_by_id(self, pos_id: UUID) -> Optional[CommodityPosition]:
        return self._positions.get(pos_id)

    async def find_positions_by_portfolio(self, portfolio_id: UUID) -> List[CommodityPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def find_positions_by_type(self, comm_type: CommodityType) -> List[CommodityPosition]:
        return [p for p in self._positions.values() if p.commodity_type == comm_type]

    async def save_curve(self, curve: CommodityCurve) -> CommodityCurve:
        self._curves[curve.curve_id] = curve
        return curve

    async def find_curve_by_commodity(self, commodity_name: str) -> Optional[CommodityCurve]:
        for curve in sorted(self._curves.values(), key=lambda x: x.curve_date, reverse=True):
            if curve.commodity_name == commodity_name:
                return curve
        return None

    async def save_exposure(self, exposure: CommodityExposure) -> CommodityExposure:
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def save_scenario(self, scenario: CommodityScenario) -> CommodityScenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_statistics(self) -> Dict[str, Any]:
        return {"total_positions": len(self._positions), "total_curves": len(self._curves)}


commodity_repository = CommodityRepository()
