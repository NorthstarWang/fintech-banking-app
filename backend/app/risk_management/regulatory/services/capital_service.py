"""Capital Service - Business logic for regulatory capital management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.capital_models import (
    CapitalInstrument, CapitalDeduction, CapitalPosition, CapitalPlan,
    StressTestCapital, CapitalLimit, CapitalAllocation, CapitalReport,
    CapitalInstrumentType, DeductionType, CapitalTier
)
from ..repositories.capital_repository import capital_repository


class CapitalService:
    def __init__(self):
        self.repository = capital_repository

    async def register_instrument(
        self, instrument_code: str, instrument_type: CapitalInstrumentType, tier: str,
        issuer: str, issue_date: date, nominal_amount: Decimal, carrying_amount: Decimal,
        eligible_amount: Decimal, **kwargs
    ) -> CapitalInstrument:
        instrument = CapitalInstrument(
            instrument_code=instrument_code, instrument_type=instrument_type, tier=tier,
            issuer=issuer, issue_date=issue_date, nominal_amount=nominal_amount,
            carrying_amount=carrying_amount, eligible_amount=eligible_amount, **kwargs
        )
        await self.repository.save_instrument(instrument)
        return instrument

    async def record_deduction(
        self, reporting_date: date, deduction_type: DeductionType, tier: str,
        gross_amount: Decimal, deduction_amount: Decimal, description: str, reference: str, methodology: str
    ) -> CapitalDeduction:
        deduction = CapitalDeduction(
            reporting_date=reporting_date, deduction_type=deduction_type, tier=tier,
            gross_amount=gross_amount, deduction_amount=deduction_amount, description=description,
            reference=reference, methodology=methodology
        )
        await self.repository.save_deduction(deduction)
        return deduction

    async def calculate_capital_position(
        self, reporting_date: date, entity_id: str
    ) -> CapitalPosition:
        instruments = await self.repository.find_all_instruments()
        deductions = await self.repository.find_deductions_by_date(reporting_date)

        cet1_instruments = [i for i in instruments if i.tier == "CET1" and i.is_active]
        at1_instruments = [i for i in instruments if i.tier == "AT1" and i.is_active]
        tier2_instruments = [i for i in instruments if i.tier == "Tier2" and i.is_active]

        cet1_gross = sum(i.eligible_amount for i in cet1_instruments)
        at1_gross = sum(i.eligible_amount for i in at1_instruments)
        tier2_gross = sum(i.eligible_amount for i in tier2_instruments)

        cet1_deductions = sum(d.deduction_amount for d in deductions if d.tier == "CET1")
        at1_deductions = sum(d.deduction_amount for d in deductions if d.tier == "AT1")
        tier2_deductions = sum(d.deduction_amount for d in deductions if d.tier == "Tier2")

        cet1_net = cet1_gross - cet1_deductions
        at1_net = at1_gross - at1_deductions
        tier1 = cet1_net + at1_net
        tier2_net = tier2_gross - tier2_deductions
        total_capital = tier1 + tier2_net

        total_rwa = Decimal("1000000000")

        position = CapitalPosition(
            reporting_date=reporting_date, entity_id=entity_id,
            cet1_gross=cet1_gross, cet1_deductions=cet1_deductions, cet1_adjustments=Decimal("0"), cet1_net=cet1_net,
            at1_gross=at1_gross, at1_deductions=at1_deductions, at1_net=at1_net, tier1_capital=tier1,
            tier2_gross=tier2_gross, tier2_deductions=tier2_deductions, tier2_net=tier2_net,
            total_capital=total_capital, total_rwa=total_rwa,
            cet1_ratio=cet1_net / total_rwa * 100, tier1_ratio=tier1 / total_rwa * 100,
            total_capital_ratio=total_capital / total_rwa * 100,
            leverage_exposure=total_rwa * Decimal("1.2"), leverage_ratio=tier1 / (total_rwa * Decimal("1.2")) * 100
        )
        await self.repository.save_position(position)
        return position

    async def create_capital_plan(
        self, plan_name: str, plan_year: int, entity_id: str, baseline_capital: Decimal,
        target_cet1_ratio: Decimal, target_tier1_ratio: Decimal, target_total_ratio: Decimal,
        planned_issuances: List[Dict[str, Any]], planned_redemptions: List[Dict[str, Any]]
    ) -> CapitalPlan:
        plan = CapitalPlan(
            plan_name=plan_name, plan_year=plan_year, entity_id=entity_id, baseline_capital=baseline_capital,
            target_cet1_ratio=target_cet1_ratio, target_tier1_ratio=target_tier1_ratio,
            target_total_ratio=target_total_ratio, planned_issuances=planned_issuances,
            planned_redemptions=planned_redemptions, dividend_assumptions={}, rwa_projections={},
            stress_scenario_results={}, contingency_actions=[]
        )
        await self.repository.save_plan(plan)
        return plan

    async def run_stress_test(
        self, scenario_name: str, scenario_type: str, starting_capital: Decimal,
        credit_losses: Decimal, market_losses: Decimal, operational_losses: Decimal
    ) -> StressTestCapital:
        total_impact = credit_losses + market_losses + operational_losses
        projected_capital = starting_capital - total_impact

        stress = StressTestCapital(
            scenario_name=scenario_name, scenario_type=scenario_type, reporting_date=date.today(),
            projection_period="9 quarters", starting_capital=starting_capital, projected_capital=projected_capital,
            capital_impact=total_impact, rwa_impact=Decimal("0"), pre_provision_net_revenue=Decimal("0"),
            credit_losses=credit_losses, market_losses=market_losses, operational_losses=operational_losses,
            other_impacts=Decimal("0"), minimum_cet1_ratio=Decimal("4.5"), minimum_tier1_ratio=Decimal("6"),
            minimum_total_ratio=Decimal("8"), capital_shortfall=max(Decimal("0"), Decimal("0") - projected_capital),
            management_actions=[]
        )
        await self.repository.save_stress_test(stress)
        return stress

    async def set_capital_limit(
        self, limit_type: str, metric: str, minimum_value: Decimal, warning_threshold: Decimal,
        target_value: Decimal, approved_by: str
    ) -> CapitalLimit:
        limit = CapitalLimit(
            limit_type=limit_type, metric=metric, minimum_value=minimum_value,
            warning_threshold=warning_threshold, target_value=target_value, current_value=Decimal("0"),
            headroom=Decimal("0"), status="green", effective_date=date.today(),
            review_date=date.today(), approved_by=approved_by
        )
        await self.repository.save_limit(limit)
        return limit

    async def generate_report(self, entity_id: str, generated_by: str) -> CapitalReport:
        position = await self.repository.find_latest_position(entity_id)
        instruments = await self.repository.find_all_instruments()

        report = CapitalReport(
            report_date=date.today(), report_type="quarterly", entity_id=entity_id,
            total_capital=position.total_capital if position else Decimal("0"),
            cet1_ratio=position.cet1_ratio if position else Decimal("0"),
            tier1_ratio=position.tier1_ratio if position else Decimal("0"),
            total_ratio=position.total_capital_ratio if position else Decimal("0"),
            leverage_ratio=position.leverage_ratio if position else Decimal("0"),
            capital_surplus=Decimal("0"), rwa_total=position.total_rwa if position else Decimal("0"),
            rwa_density=Decimal("0"), capital_instruments_count=len(instruments),
            upcoming_maturities=[], stress_test_results={}, regulatory_requirements={}, buffer_utilization={},
            generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


capital_service = CapitalService()
