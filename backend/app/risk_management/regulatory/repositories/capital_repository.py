"""Capital Repository - Data access for regulatory capital management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.capital_models import (
    CapitalInstrument, CapitalDeduction, CapitalPosition, CapitalPlan,
    StressTestCapital, CapitalLimit, CapitalAllocation, CapitalReport
)


class CapitalRepository:
    def __init__(self):
        self._instruments: Dict[UUID, CapitalInstrument] = {}
        self._deductions: Dict[UUID, CapitalDeduction] = {}
        self._positions: Dict[UUID, CapitalPosition] = {}
        self._plans: Dict[UUID, CapitalPlan] = {}
        self._stress_tests: Dict[UUID, StressTestCapital] = {}
        self._limits: Dict[UUID, CapitalLimit] = {}
        self._allocations: Dict[UUID, CapitalAllocation] = {}
        self._reports: Dict[UUID, CapitalReport] = {}

    async def save_instrument(self, instrument: CapitalInstrument) -> None:
        self._instruments[instrument.instrument_id] = instrument

    async def find_instrument_by_id(self, instrument_id: UUID) -> Optional[CapitalInstrument]:
        return self._instruments.get(instrument_id)

    async def find_all_instruments(self) -> List[CapitalInstrument]:
        return list(self._instruments.values())

    async def find_instruments_by_tier(self, tier: str) -> List[CapitalInstrument]:
        return [i for i in self._instruments.values() if i.tier == tier]

    async def find_active_instruments(self) -> List[CapitalInstrument]:
        return [i for i in self._instruments.values() if i.is_active]

    async def find_instruments_maturing_before(self, before_date: date) -> List[CapitalInstrument]:
        return [i for i in self._instruments.values() if i.maturity_date and i.maturity_date <= before_date]

    async def save_deduction(self, deduction: CapitalDeduction) -> None:
        self._deductions[deduction.deduction_id] = deduction

    async def find_deduction_by_id(self, deduction_id: UUID) -> Optional[CapitalDeduction]:
        return self._deductions.get(deduction_id)

    async def find_all_deductions(self) -> List[CapitalDeduction]:
        return list(self._deductions.values())

    async def find_deductions_by_date(self, reporting_date: date) -> List[CapitalDeduction]:
        return [d for d in self._deductions.values() if d.reporting_date == reporting_date]

    async def find_deductions_by_tier(self, tier: str) -> List[CapitalDeduction]:
        return [d for d in self._deductions.values() if d.tier == tier]

    async def save_position(self, position: CapitalPosition) -> None:
        self._positions[position.position_id] = position

    async def find_position_by_id(self, position_id: UUID) -> Optional[CapitalPosition]:
        return self._positions.get(position_id)

    async def find_all_positions(self) -> List[CapitalPosition]:
        return list(self._positions.values())

    async def find_positions_by_entity(self, entity_id: str) -> List[CapitalPosition]:
        return [p for p in self._positions.values() if p.entity_id == entity_id]

    async def find_latest_position(self, entity_id: str) -> Optional[CapitalPosition]:
        positions = [p for p in self._positions.values() if p.entity_id == entity_id]
        return max(positions, key=lambda x: x.reporting_date) if positions else None

    async def save_plan(self, plan: CapitalPlan) -> None:
        self._plans[plan.plan_id] = plan

    async def find_plan_by_id(self, plan_id: UUID) -> Optional[CapitalPlan]:
        return self._plans.get(plan_id)

    async def find_all_plans(self) -> List[CapitalPlan]:
        return list(self._plans.values())

    async def find_plans_by_year(self, year: int) -> List[CapitalPlan]:
        return [p for p in self._plans.values() if p.plan_year == year]

    async def find_approved_plans(self) -> List[CapitalPlan]:
        return [p for p in self._plans.values() if p.status == "approved"]

    async def save_stress_test(self, stress_test: StressTestCapital) -> None:
        self._stress_tests[stress_test.stress_test_id] = stress_test

    async def find_stress_test_by_id(self, stress_test_id: UUID) -> Optional[StressTestCapital]:
        return self._stress_tests.get(stress_test_id)

    async def find_all_stress_tests(self) -> List[StressTestCapital]:
        return list(self._stress_tests.values())

    async def find_stress_tests_by_scenario(self, scenario_type: str) -> List[StressTestCapital]:
        return [s for s in self._stress_tests.values() if s.scenario_type == scenario_type]

    async def save_limit(self, limit: CapitalLimit) -> None:
        self._limits[limit.limit_id] = limit

    async def find_limit_by_id(self, limit_id: UUID) -> Optional[CapitalLimit]:
        return self._limits.get(limit_id)

    async def find_all_limits(self) -> List[CapitalLimit]:
        return list(self._limits.values())

    async def find_breached_limits(self) -> List[CapitalLimit]:
        return [l for l in self._limits.values() if l.status == "red"]

    async def save_allocation(self, allocation: CapitalAllocation) -> None:
        self._allocations[allocation.allocation_id] = allocation

    async def find_allocation_by_id(self, allocation_id: UUID) -> Optional[CapitalAllocation]:
        return self._allocations.get(allocation_id)

    async def find_all_allocations(self) -> List[CapitalAllocation]:
        return list(self._allocations.values())

    async def find_allocations_by_business_unit(self, business_unit: str) -> List[CapitalAllocation]:
        return [a for a in self._allocations.values() if a.business_unit == business_unit]

    async def save_report(self, report: CapitalReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[CapitalReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[CapitalReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_instruments": len(self._instruments),
            "active_instruments": len([i for i in self._instruments.values() if i.is_active]),
            "total_deductions": len(self._deductions),
            "total_positions": len(self._positions),
            "total_plans": len(self._plans),
            "total_stress_tests": len(self._stress_tests),
            "total_limits": len(self._limits),
            "breached_limits": len([l for l in self._limits.values() if l.status == "red"]),
            "total_allocations": len(self._allocations),
            "total_reports": len(self._reports),
        }


capital_repository = CapitalRepository()
