"""Stress Test Service - Market risk stress testing service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.stress_test_models import (
    StressScenario, StressTestResult, HistoricalScenario,
    SensitivityAnalysis, ReverseStressTest, StressTestStatistics,
    ScenarioType, ScenarioSeverity
)


class StressTestService:
    def __init__(self):
        self._scenarios: Dict[UUID, StressScenario] = {}
        self._results: Dict[UUID, StressTestResult] = {}
        self._historical: Dict[UUID, HistoricalScenario] = {}
        self._sensitivities: Dict[UUID, SensitivityAnalysis] = {}
        self._reverse_tests: Dict[UUID, ReverseStressTest] = {}
        self._initialize_scenarios()

    def _initialize_scenarios(self):
        # Pre-defined scenarios
        scenarios = [
            StressScenario(
                scenario_name="2008 Financial Crisis",
                scenario_type=ScenarioType.HISTORICAL,
                severity=ScenarioSeverity.EXTREME,
                description="Replication of 2008 financial crisis market conditions",
                equity_shocks={"SPX": -0.40, "default": -0.35},
                fx_shocks={"EURUSD": -0.10, "GBPUSD": -0.15},
                ir_shocks={"2Y": -0.02, "10Y": -0.01},
                credit_spread_shocks={"IG": 0.03, "HY": 0.08},
                created_by="system"
            ),
            StressScenario(
                scenario_name="Rate Shock +200bp",
                scenario_type=ScenarioType.HYPOTHETICAL,
                severity=ScenarioSeverity.SEVERE,
                description="Parallel rate shock of 200 basis points",
                ir_shocks={"all": 0.02},
                equity_shocks={"default": -0.10},
                created_by="system"
            ),
            StressScenario(
                scenario_name="Emerging Market Crisis",
                scenario_type=ScenarioType.HYPOTHETICAL,
                severity=ScenarioSeverity.SEVERE,
                description="EM currency and equity crisis",
                fx_shocks={"USDBRL": 0.30, "USDMXN": 0.25, "USDZAR": 0.35},
                equity_shocks={"EM": -0.25},
                created_by="system"
            )
        ]
        for scenario in scenarios:
            self._scenarios[scenario.scenario_id] = scenario

    async def create_scenario(
        self, scenario_name: str, scenario_type: ScenarioType,
        severity: ScenarioSeverity, description: str,
        shocks: Dict[str, Dict[str, float]], created_by: str
    ) -> StressScenario:
        scenario = StressScenario(
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            severity=severity,
            description=description,
            equity_shocks=shocks.get("equity", {}),
            fx_shocks=shocks.get("fx", {}),
            ir_shocks=shocks.get("ir", {}),
            credit_spread_shocks=shocks.get("credit", {}),
            commodity_shocks=shocks.get("commodity", {}),
            volatility_shocks=shocks.get("volatility", {}),
            created_by=created_by
        )
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_scenario(self, scenario_id: UUID) -> Optional[StressScenario]:
        return self._scenarios.get(scenario_id)

    async def run_stress_test(
        self, scenario_id: UUID, portfolio_id: UUID,
        portfolio_value: float, positions: List[Dict[str, Any]]
    ) -> Optional[StressTestResult]:
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            return None

        # Calculate P&L impact
        pnl_impact = 0
        position_impacts = []
        risk_contributions = {}

        for pos in positions:
            asset_class = pos.get("asset_class", "equity")
            value = pos.get("value", 0)

            if asset_class == "equity":
                shock = scenario.equity_shocks.get(pos.get("ticker", "default"),
                        scenario.equity_shocks.get("default", 0))
            elif asset_class == "fx":
                shock = scenario.fx_shocks.get(pos.get("currency_pair", ""), 0)
            elif asset_class == "rates":
                shock = scenario.ir_shocks.get(pos.get("tenor", ""),
                        scenario.ir_shocks.get("all", 0))
            else:
                shock = 0

            impact = value * shock
            pnl_impact += impact
            position_impacts.append({"position": pos.get("id"), "impact": impact})
            risk_contributions[asset_class] = risk_contributions.get(asset_class, 0) + abs(impact)

        var_change = abs(pnl_impact) * 0.1

        result = StressTestResult(
            scenario_id=scenario_id,
            portfolio_id=portfolio_id,
            test_date=date.today(),
            portfolio_value_before=portfolio_value,
            portfolio_value_after=portfolio_value + pnl_impact,
            pnl_impact=pnl_impact,
            pnl_impact_percentage=(pnl_impact / portfolio_value * 100) if portfolio_value > 0 else 0,
            var_before=portfolio_value * 0.02,
            var_after=portfolio_value * 0.02 + var_change,
            var_change=var_change,
            risk_factor_contributions=risk_contributions,
            position_level_impacts=position_impacts
        )
        self._results[result.result_id] = result
        return result

    async def run_sensitivity_analysis(
        self, portfolio_id: UUID, risk_factor: str,
        shock_sizes: List[float], base_pnl_impacts: List[float]
    ) -> SensitivityAnalysis:
        # Calculate sensitivity (first derivative) and convexity (second derivative)
        if len(shock_sizes) >= 2 and len(base_pnl_impacts) >= 2:
            sensitivity = (base_pnl_impacts[1] - base_pnl_impacts[0]) / (shock_sizes[1] - shock_sizes[0])
            if len(shock_sizes) >= 3 and len(base_pnl_impacts) >= 3:
                d1 = (base_pnl_impacts[1] - base_pnl_impacts[0]) / (shock_sizes[1] - shock_sizes[0])
                d2 = (base_pnl_impacts[2] - base_pnl_impacts[1]) / (shock_sizes[2] - shock_sizes[1])
                convexity = (d2 - d1) / ((shock_sizes[2] - shock_sizes[0]) / 2)
            else:
                convexity = 0
        else:
            sensitivity = 0
            convexity = 0

        analysis = SensitivityAnalysis(
            portfolio_id=portfolio_id,
            analysis_date=date.today(),
            risk_factor=risk_factor,
            shock_sizes=shock_sizes,
            pnl_impacts=base_pnl_impacts,
            sensitivity=sensitivity,
            convexity=convexity
        )
        self._sensitivities[analysis.analysis_id] = analysis
        return analysis

    async def run_reverse_stress_test(
        self, portfolio_id: UUID, target_loss: float, created_by: str
    ) -> ReverseStressTest:
        # Identify scenarios that could cause target loss
        scenarios = []
        for scenario in self._scenarios.values():
            estimated_impact = sum(scenario.equity_shocks.values()) * 0.5 + \
                             sum(scenario.fx_shocks.values()) * 0.3
            if abs(estimated_impact) >= target_loss * 0.8:
                scenarios.append({
                    "scenario_id": str(scenario.scenario_id),
                    "scenario_name": scenario.scenario_name,
                    "estimated_impact": estimated_impact
                })

        test = ReverseStressTest(
            portfolio_id=portfolio_id,
            test_date=date.today(),
            target_loss=target_loss,
            identified_scenarios=scenarios,
            probability_assessment="medium" if scenarios else "low",
            plausibility_score=60 if scenarios else 30,
            created_by=created_by
        )
        self._reverse_tests[test.test_id] = test
        return test

    async def get_all_scenarios(self) -> List[StressScenario]:
        return list(self._scenarios.values())

    async def get_statistics(self) -> StressTestStatistics:
        stats = StressTestStatistics(
            total_scenarios=len(self._scenarios),
            total_tests_run=len(self._results)
        )
        if self._results:
            stats.average_pnl_impact = sum(r.pnl_impact for r in self._results.values()) / len(self._results)
            stats.worst_case_loss = min(r.pnl_impact for r in self._results.values())
        for scenario in self._scenarios.values():
            stats.by_severity[scenario.severity.value] = stats.by_severity.get(scenario.severity.value, 0) + 1
        return stats


stress_test_service = StressTestService()
