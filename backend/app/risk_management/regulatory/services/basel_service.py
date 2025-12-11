"""Basel Service - Business logic for Basel III/IV compliance"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.basel_models import (
    BaselCapitalRequirement, CreditRiskRWA, MarketRiskRWA, OperationalRiskRWA,
    LeverageRatio, LiquidityCoverageRatio, NetStableFundingRatio, CapitalBuffer,
    BaselReport, RiskCategory
)
from ..repositories.basel_repository import basel_repository


class BaselService:
    def __init__(self):
        self.repository = basel_repository

    async def calculate_credit_rwa(
        self, reporting_date: date, asset_class: str, approach: str,
        exposure_amount: Decimal, risk_weight: Decimal, **kwargs
    ) -> CreditRiskRWA:
        rwa_amount = exposure_amount * risk_weight / 100
        rwa = CreditRiskRWA(
            reporting_date=reporting_date, asset_class=asset_class, approach=approach,
            exposure_amount=exposure_amount, risk_weight=risk_weight, rwa_amount=rwa_amount,
            **kwargs
        )
        await self.repository.save_credit_rwa(rwa)
        return rwa

    async def calculate_market_rwa(
        self, reporting_date: date, approach: str, desk_id: str, risk_type: str,
        sensitivities_based: Decimal, default_risk_charge: Decimal, residual_risk_addon: Decimal
    ) -> MarketRiskRWA:
        total_rwa = sensitivities_based + default_risk_charge + residual_risk_addon
        rwa = MarketRiskRWA(
            reporting_date=reporting_date, approach=approach, desk_id=desk_id,
            risk_type=risk_type, sensitivities_based=sensitivities_based,
            default_risk_charge=default_risk_charge, residual_risk_addon=residual_risk_addon,
            total_rwa=total_rwa
        )
        await self.repository.save_market_rwa(rwa)
        return rwa

    async def calculate_operational_rwa(
        self, reporting_date: date, approach: str, business_indicator: Decimal,
        loss_component: Decimal
    ) -> OperationalRiskRWA:
        bi_component = business_indicator * Decimal("0.12")
        ilm = Decimal("1.0") if loss_component == 0 else min(Decimal("1.5"), loss_component / bi_component)
        total_rwa = bi_component * ilm * Decimal("12.5")
        rwa = OperationalRiskRWA(
            reporting_date=reporting_date, approach=approach, business_indicator=business_indicator,
            bi_component=bi_component, ilm=ilm, loss_component=loss_component, total_rwa=total_rwa
        )
        await self.repository.save_operational_rwa(rwa)
        return rwa

    async def calculate_leverage_ratio(
        self, reporting_date: date, entity_id: str, tier1_capital: Decimal,
        on_balance_sheet: Decimal, derivatives_exposure: Decimal,
        sft_exposure: Decimal, off_balance_sheet: Decimal
    ) -> LeverageRatio:
        total_exposure = on_balance_sheet + derivatives_exposure + sft_exposure + off_balance_sheet
        leverage_ratio = (tier1_capital / total_exposure * 100) if total_exposure > 0 else Decimal("0")
        ratio = LeverageRatio(
            reporting_date=reporting_date, entity_id=entity_id, tier1_capital=tier1_capital,
            total_exposure=total_exposure, on_balance_sheet=on_balance_sheet,
            derivatives_exposure=derivatives_exposure, sft_exposure=sft_exposure,
            off_balance_sheet=off_balance_sheet, leverage_ratio=leverage_ratio,
            minimum_requirement=Decimal("3"), is_compliant=leverage_ratio >= Decimal("3")
        )
        await self.repository.save_leverage_ratio(ratio)
        return ratio

    async def calculate_lcr(
        self, reporting_date: date, entity_id: str, hqla_level1: Decimal,
        hqla_level2a: Decimal, hqla_level2b: Decimal, gross_outflows: Decimal, gross_inflows: Decimal
    ) -> LiquidityCoverageRatio:
        total_hqla = hqla_level1 + (hqla_level2a * Decimal("0.85")) + (hqla_level2b * Decimal("0.50"))
        capped_inflows = min(gross_inflows, gross_outflows * Decimal("0.75"))
        net_outflows = gross_outflows - capped_inflows
        lcr_ratio = (total_hqla / net_outflows * 100) if net_outflows > 0 else Decimal("0")
        lcr = LiquidityCoverageRatio(
            reporting_date=reporting_date, entity_id=entity_id, hqla_level1=hqla_level1,
            hqla_level2a=hqla_level2a, hqla_level2b=hqla_level2b, total_hqla=total_hqla,
            gross_outflows=gross_outflows, gross_inflows=gross_inflows, net_cash_outflows=net_outflows,
            lcr_ratio=lcr_ratio, minimum_requirement=Decimal("100"), is_compliant=lcr_ratio >= Decimal("100")
        )
        await self.repository.save_lcr(lcr)
        return lcr

    async def calculate_nsfr(
        self, reporting_date: date, entity_id: str, asf_components: Dict[str, Decimal],
        rsf_components: Dict[str, Decimal]
    ) -> NetStableFundingRatio:
        available = sum(asf_components.values())
        required = sum(rsf_components.values())
        nsfr_ratio = (available / required * 100) if required > 0 else Decimal("0")
        nsfr = NetStableFundingRatio(
            reporting_date=reporting_date, entity_id=entity_id, available_stable_funding=available,
            required_stable_funding=required, asf_components=asf_components, rsf_components=rsf_components,
            nsfr_ratio=nsfr_ratio, minimum_requirement=Decimal("100"), is_compliant=nsfr_ratio >= Decimal("100")
        )
        await self.repository.save_nsfr(nsfr)
        return nsfr

    async def generate_basel_report(
        self, reporting_date: date, entity_id: str, generated_by: str
    ) -> BaselReport:
        credit_rwas = await self.repository.find_credit_rwa_by_date(reporting_date)
        market_rwas = await self.repository.find_market_rwa_by_date(reporting_date)
        op_rwas = await self.repository.find_operational_rwa_by_date(reporting_date)

        credit_total = sum(r.rwa_amount for r in credit_rwas)
        market_total = sum(r.total_rwa for r in market_rwas)
        op_total = sum(r.total_rwa for r in op_rwas)
        total_rwa = credit_total + market_total + op_total

        report = BaselReport(
            report_type="quarterly", reporting_date=reporting_date, entity_id=entity_id,
            total_rwa=total_rwa, credit_risk_rwa=credit_total, market_risk_rwa=market_total,
            operational_risk_rwa=op_total, cet1_capital=Decimal("0"), at1_capital=Decimal("0"),
            tier2_capital=Decimal("0"), total_capital=Decimal("0"), cet1_ratio=Decimal("0"),
            tier1_ratio=Decimal("0"), total_capital_ratio=Decimal("0"), leverage_ratio=Decimal("0"),
            lcr=Decimal("0"), nsfr=Decimal("0"), generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


basel_service = BaselService()
