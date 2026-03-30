"""Stress Test Repository - Data access layer for stress testing"""

from typing import Any
from uuid import UUID

from ..models.stress_test_models import (
    HistoricalScenario,
    ReverseStressTest,
    SensitivityAnalysis,
    StressScenario,
    StressTestResult,
)


class StressTestRepository:
    def __init__(self):
        self._scenarios: dict[UUID, StressScenario] = {}
        self._results: dict[UUID, StressTestResult] = {}
        self._historical: dict[UUID, HistoricalScenario] = {}
        self._sensitivities: dict[UUID, SensitivityAnalysis] = {}
        self._reverse_tests: dict[UUID, ReverseStressTest] = {}

    async def save_scenario(self, scenario: StressScenario) -> StressScenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def find_scenario_by_id(self, scenario_id: UUID) -> StressScenario | None:
        return self._scenarios.get(scenario_id)

    async def find_active_scenarios(self) -> list[StressScenario]:
        return [s for s in self._scenarios.values() if s.is_active]

    async def save_result(self, result: StressTestResult) -> StressTestResult:
        self._results[result.result_id] = result
        return result

    async def find_results_by_portfolio(self, portfolio_id: UUID) -> list[StressTestResult]:
        return [r for r in self._results.values() if r.portfolio_id == portfolio_id]

    async def find_results_by_scenario(self, scenario_id: UUID) -> list[StressTestResult]:
        return [r for r in self._results.values() if r.scenario_id == scenario_id]

    async def save_historical(self, historical: HistoricalScenario) -> HistoricalScenario:
        self._historical[historical.scenario_id] = historical
        return historical

    async def save_sensitivity(self, sensitivity: SensitivityAnalysis) -> SensitivityAnalysis:
        self._sensitivities[sensitivity.analysis_id] = sensitivity
        return sensitivity

    async def save_reverse_test(self, test: ReverseStressTest) -> ReverseStressTest:
        self._reverse_tests[test.test_id] = test
        return test

    async def get_statistics(self) -> dict[str, Any]:
        return {"total_scenarios": len(self._scenarios), "total_results": len(self._results)}


stress_test_repository = StressTestRepository()
