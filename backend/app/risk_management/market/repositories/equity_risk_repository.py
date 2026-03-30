"""Equity Risk Repository - Data access layer for equity risk"""

from typing import Any
from uuid import UUID

from ..models.equity_risk_models import (
    BetaAnalysis,
    EquityExposure,
    EquityFactorExposure,
    EquityPosition,
    EquityScenario,
)


class EquityRiskRepository:
    def __init__(self):
        self._positions: dict[UUID, EquityPosition] = {}
        self._exposures: dict[UUID, EquityExposure] = {}
        self._beta_analyses: dict[UUID, BetaAnalysis] = {}
        self._factor_exposures: dict[UUID, EquityFactorExposure] = {}
        self._scenarios: dict[UUID, EquityScenario] = {}

    async def save_position(self, position: EquityPosition) -> EquityPosition:
        self._positions[position.position_id] = position
        return position

    async def find_position_by_id(self, pos_id: UUID) -> EquityPosition | None:
        return self._positions.get(pos_id)

    async def find_positions_by_portfolio(self, portfolio_id: UUID) -> list[EquityPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def find_positions_by_sector(self, sector: str) -> list[EquityPosition]:
        return [p for p in self._positions.values() if p.sector == sector]

    async def save_exposure(self, exposure: EquityExposure) -> EquityExposure:
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def save_beta_analysis(self, analysis: BetaAnalysis) -> BetaAnalysis:
        self._beta_analyses[analysis.analysis_id] = analysis
        return analysis

    async def find_beta_by_portfolio(self, portfolio_id: UUID) -> list[BetaAnalysis]:
        return [b for b in self._beta_analyses.values() if b.portfolio_id == portfolio_id]

    async def save_factor_exposure(self, exposure: EquityFactorExposure) -> EquityFactorExposure:
        self._factor_exposures[exposure.exposure_id] = exposure
        return exposure

    async def save_scenario(self, scenario: EquityScenario) -> EquityScenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_statistics(self) -> dict[str, Any]:
        return {"total_positions": len(self._positions), "total_analyses": len(self._beta_analyses)}


equity_risk_repository = EquityRiskRepository()
