"""Interest Rate Service - Interest rate risk management service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.interest_rate_models import (
    InterestRateCurve, DurationAnalysis, GapAnalysis,
    RateShockScenario, InterestRateRisk, InterestRateStatistics,
    CurveType
)


class InterestRateService:
    def __init__(self):
        self._curves: Dict[UUID, InterestRateCurve] = {}
        self._duration_analyses: Dict[UUID, DurationAnalysis] = {}
        self._gap_analyses: Dict[UUID, GapAnalysis] = {}
        self._scenarios: Dict[UUID, RateShockScenario] = {}
        self._risks: Dict[UUID, InterestRateRisk] = {}

    async def create_curve(
        self, curve_name: str, curve_type: CurveType, currency: str,
        tenors: List[str], rates: List[float], source: str
    ) -> InterestRateCurve:
        curve = InterestRateCurve(
            curve_name=curve_name,
            curve_type=curve_type,
            currency=currency,
            reference_date=date.today(),
            tenors=tenors,
            rates=rates,
            source=source
        )
        self._curves[curve.curve_id] = curve
        return curve

    async def get_curve(self, curve_id: UUID) -> Optional[InterestRateCurve]:
        return self._curves.get(curve_id)

    async def calculate_duration(
        self, portfolio_id: UUID, portfolio_value: float,
        cash_flows: List[Dict[str, float]], yield_rate: float
    ) -> DurationAnalysis:
        # Simplified duration calculation
        weighted_time = sum(
            cf.get("time", 0) * cf.get("amount", 0) / (1 + yield_rate) ** cf.get("time", 0)
            for cf in cash_flows
        )
        pv = sum(cf.get("amount", 0) / (1 + yield_rate) ** cf.get("time", 0) for cf in cash_flows)

        macaulay_duration = weighted_time / pv if pv > 0 else 0
        modified_duration = macaulay_duration / (1 + yield_rate)
        dv01 = modified_duration * portfolio_value / 10000

        analysis = DurationAnalysis(
            portfolio_id=portfolio_id,
            analysis_date=date.today(),
            modified_duration=modified_duration,
            macaulay_duration=macaulay_duration,
            effective_duration=modified_duration * 1.05,
            dollar_duration=modified_duration * portfolio_value,
            dv01=dv01,
            convexity=macaulay_duration ** 2 * 0.01,
            portfolio_value=portfolio_value,
            yield_to_maturity=yield_rate
        )
        self._duration_analyses[analysis.analysis_id] = analysis
        return analysis

    async def perform_gap_analysis(
        self, time_buckets: List[str],
        assets: List[float], liabilities: List[float]
    ) -> GapAnalysis:
        gaps = [a - l for a, l in zip(assets, liabilities)]
        cumulative = []
        running_total = 0
        for gap in gaps:
            running_total += gap
            cumulative.append(running_total)
        ratios = [a / l if l > 0 else 0 for a, l in zip(assets, liabilities)]

        analysis = GapAnalysis(
            analysis_date=date.today(),
            time_buckets=time_buckets,
            rate_sensitive_assets=assets,
            rate_sensitive_liabilities=liabilities,
            gap_amounts=gaps,
            cumulative_gap=cumulative,
            gap_ratio=ratios,
            net_interest_income_impact=sum(gaps) * 0.01
        )
        self._gap_analyses[analysis.analysis_id] = analysis
        return analysis

    async def create_shock_scenario(
        self, scenario_name: str, scenario_type: str,
        base_curve_id: UUID, shock_amounts: Dict[str, float]
    ) -> RateShockScenario:
        base_curve = self._curves.get(base_curve_id)
        stressed_rates = {}
        if base_curve:
            for tenor, rate in zip(base_curve.tenors, base_curve.rates):
                shock = shock_amounts.get(tenor, shock_amounts.get("all", 0))
                stressed_rates[tenor] = rate + shock

        scenario = RateShockScenario(
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            shock_amounts=shock_amounts,
            base_curve_id=base_curve_id,
            stressed_rates=stressed_rates,
            pnl_impact=0,
            duration_impact=0
        )
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def assess_ir_risk(self, portfolio_id: UUID) -> InterestRateRisk:
        risk = InterestRateRisk(
            portfolio_id=portfolio_id,
            assessment_date=date.today(),
            repricing_risk=0.02,
            yield_curve_risk=0.01,
            basis_risk=0.005,
            optionality_risk=0.003,
            total_ir_risk=0.038,
            economic_value_sensitivity=0.05,
            earnings_at_risk=0.02,
            net_interest_income_at_risk=0.015
        )
        self._risks[risk.risk_id] = risk
        return risk

    async def get_statistics(self) -> InterestRateStatistics:
        stats = InterestRateStatistics(total_curves=len(self._curves))
        if self._duration_analyses:
            stats.average_duration = sum(d.modified_duration for d in self._duration_analyses.values()) / len(self._duration_analyses)
            stats.total_dv01 = sum(d.dv01 for d in self._duration_analyses.values())
        for curve in self._curves.values():
            stats.by_currency[curve.currency] = stats.by_currency.get(curve.currency, 0) + 1
        return stats


interest_rate_service = InterestRateService()
