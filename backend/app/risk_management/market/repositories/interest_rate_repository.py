"""Interest Rate Repository - Data access layer for interest rate risk"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.interest_rate_models import InterestRateCurve, DurationAnalysis, GapAnalysis, RateShockScenario, InterestRateRisk


class InterestRateRepository:
    def __init__(self):
        self._curves: Dict[UUID, InterestRateCurve] = {}
        self._duration_analyses: Dict[UUID, DurationAnalysis] = {}
        self._gap_analyses: Dict[UUID, GapAnalysis] = {}
        self._scenarios: Dict[UUID, RateShockScenario] = {}
        self._risks: Dict[UUID, InterestRateRisk] = {}

    async def save_curve(self, curve: InterestRateCurve) -> InterestRateCurve:
        self._curves[curve.curve_id] = curve
        return curve

    async def find_curve_by_id(self, curve_id: UUID) -> Optional[InterestRateCurve]:
        return self._curves.get(curve_id)

    async def find_curves_by_currency(self, currency: str) -> List[InterestRateCurve]:
        return [c for c in self._curves.values() if c.currency == currency]

    async def save_duration_analysis(self, analysis: DurationAnalysis) -> DurationAnalysis:
        self._duration_analyses[analysis.analysis_id] = analysis
        return analysis

    async def find_duration_by_portfolio(self, portfolio_id: UUID) -> List[DurationAnalysis]:
        return [d for d in self._duration_analyses.values() if d.portfolio_id == portfolio_id]

    async def save_gap_analysis(self, analysis: GapAnalysis) -> GapAnalysis:
        self._gap_analyses[analysis.analysis_id] = analysis
        return analysis

    async def save_scenario(self, scenario: RateShockScenario) -> RateShockScenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def save_risk(self, risk: InterestRateRisk) -> InterestRateRisk:
        self._risks[risk.risk_id] = risk
        return risk

    async def get_statistics(self) -> Dict[str, Any]:
        return {"total_curves": len(self._curves), "total_analyses": len(self._duration_analyses)}


interest_rate_repository = InterestRateRepository()
