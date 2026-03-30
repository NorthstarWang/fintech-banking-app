"""Basel Repository - Data access for Basel III/IV compliance"""

from datetime import date
from typing import Any
from uuid import UUID

from ..models.basel_models import (
    BaselReport,
    CapitalRequirement,
    CounterpartyCreditRisk,
    LargeExposure,
    LeverageRatio,
    LiquidityCoverageRatio,
    NetStableFundingRatio,
    RiskWeightedAsset,
)


class BaselRepository:
    def __init__(self):
        self._rwas: dict[UUID, RiskWeightedAsset] = {}
        self._capital_requirements: dict[UUID, CapitalRequirement] = {}
        self._lcrs: dict[UUID, LiquidityCoverageRatio] = {}
        self._nsfrs: dict[UUID, NetStableFundingRatio] = {}
        self._leverage_ratios: dict[UUID, LeverageRatio] = {}
        self._ccrs: dict[UUID, CounterpartyCreditRisk] = {}
        self._large_exposures: dict[UUID, LargeExposure] = {}
        self._reports: dict[UUID, BaselReport] = {}

    async def save_rwa(self, rwa: RiskWeightedAsset) -> None:
        self._rwas[rwa.rwa_id] = rwa

    async def find_rwa_by_id(self, rwa_id: UUID) -> RiskWeightedAsset | None:
        return self._rwas.get(rwa_id)

    async def find_all_rwas(self) -> list[RiskWeightedAsset]:
        return list(self._rwas.values())

    async def find_rwas_by_date(self, reporting_date: date) -> list[RiskWeightedAsset]:
        return [r for r in self._rwas.values() if r.reporting_date == reporting_date]

    async def find_rwas_by_type(self, risk_type: str) -> list[RiskWeightedAsset]:
        return [r for r in self._rwas.values() if r.risk_type.value == risk_type]

    async def save_capital_requirement(self, req: CapitalRequirement) -> None:
        self._capital_requirements[req.requirement_id] = req

    async def find_capital_requirement_by_id(self, req_id: UUID) -> CapitalRequirement | None:
        return self._capital_requirements.get(req_id)

    async def find_all_capital_requirements(self) -> list[CapitalRequirement]:
        return list(self._capital_requirements.values())

    async def find_latest_capital_requirement(self, entity_id: str) -> CapitalRequirement | None:
        reqs = [r for r in self._capital_requirements.values() if r.entity_id == entity_id]
        return max(reqs, key=lambda x: x.reporting_date) if reqs else None

    async def save_lcr(self, lcr: LiquidityCoverageRatio) -> None:
        self._lcrs[lcr.lcr_id] = lcr

    async def find_lcr_by_id(self, lcr_id: UUID) -> LiquidityCoverageRatio | None:
        return self._lcrs.get(lcr_id)

    async def find_all_lcrs(self) -> list[LiquidityCoverageRatio]:
        return list(self._lcrs.values())

    async def find_lcrs_by_entity(self, entity_id: str) -> list[LiquidityCoverageRatio]:
        return [l for l in self._lcrs.values() if l.entity_id == entity_id]

    async def save_nsfr(self, nsfr: NetStableFundingRatio) -> None:
        self._nsfrs[nsfr.nsfr_id] = nsfr

    async def find_nsfr_by_id(self, nsfr_id: UUID) -> NetStableFundingRatio | None:
        return self._nsfrs.get(nsfr_id)

    async def find_all_nsfrs(self) -> list[NetStableFundingRatio]:
        return list(self._nsfrs.values())

    async def find_nsfrs_by_entity(self, entity_id: str) -> list[NetStableFundingRatio]:
        return [n for n in self._nsfrs.values() if n.entity_id == entity_id]

    async def save_leverage_ratio(self, ratio: LeverageRatio) -> None:
        self._leverage_ratios[ratio.leverage_id] = ratio

    async def find_leverage_ratio_by_id(self, ratio_id: UUID) -> LeverageRatio | None:
        return self._leverage_ratios.get(ratio_id)

    async def find_all_leverage_ratios(self) -> list[LeverageRatio]:
        return list(self._leverage_ratios.values())

    async def save_ccr(self, ccr: CounterpartyCreditRisk) -> None:
        self._ccrs[ccr.ccr_id] = ccr

    async def find_ccr_by_id(self, ccr_id: UUID) -> CounterpartyCreditRisk | None:
        return self._ccrs.get(ccr_id)

    async def find_all_ccrs(self) -> list[CounterpartyCreditRisk]:
        return list(self._ccrs.values())

    async def find_ccrs_by_counterparty(self, counterparty_id: str) -> list[CounterpartyCreditRisk]:
        return [c for c in self._ccrs.values() if c.counterparty_id == counterparty_id]

    async def save_large_exposure(self, exposure: LargeExposure) -> None:
        self._large_exposures[exposure.exposure_id] = exposure

    async def find_large_exposure_by_id(self, exposure_id: UUID) -> LargeExposure | None:
        return self._large_exposures.get(exposure_id)

    async def find_all_large_exposures(self) -> list[LargeExposure]:
        return list(self._large_exposures.values())

    async def find_large_exposures_breached(self) -> list[LargeExposure]:
        return [e for e in self._large_exposures.values() if e.limit_breach]

    async def save_report(self, report: BaselReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> BaselReport | None:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> list[BaselReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_rwas": len(self._rwas),
            "total_capital_requirements": len(self._capital_requirements),
            "total_lcrs": len(self._lcrs),
            "total_nsfrs": len(self._nsfrs),
            "total_leverage_ratios": len(self._leverage_ratios),
            "total_ccrs": len(self._ccrs),
            "total_large_exposures": len(self._large_exposures),
            "total_reports": len(self._reports),
        }


basel_repository = BaselRepository()
