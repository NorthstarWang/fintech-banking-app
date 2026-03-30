"""KRI Repository - Data access layer for Key Risk Indicators"""

from typing import Any
from uuid import UUID

from ..models.kri_models import (
    KeyRiskIndicator,
    KRIDashboard,
    KRIMeasurement,
    KRIReport,
    KRITarget,
    KRIThresholdBreach,
    KRITrendAnalysis,
)


class KRIRepository:
    def __init__(self):
        self._kris: dict[UUID, KeyRiskIndicator] = {}
        self._measurements: dict[UUID, KRIMeasurement] = {}
        self._breaches: dict[UUID, KRIThresholdBreach] = {}
        self._targets: dict[UUID, KRITarget] = {}
        self._trend_analyses: dict[UUID, KRITrendAnalysis] = {}
        self._dashboards: dict[UUID, KRIDashboard] = {}
        self._reports: dict[UUID, KRIReport] = {}

    async def save_kri(self, kri: KeyRiskIndicator) -> KeyRiskIndicator:
        self._kris[kri.kri_id] = kri
        return kri

    async def find_kri_by_id(self, kri_id: UUID) -> KeyRiskIndicator | None:
        return self._kris.get(kri_id)

    async def find_kri_by_code(self, kri_code: str) -> KeyRiskIndicator | None:
        for kri in self._kris.values():
            if kri.kri_code == kri_code:
                return kri
        return None

    async def find_all_kris(self) -> list[KeyRiskIndicator]:
        return list(self._kris.values())

    async def update_kri(self, kri: KeyRiskIndicator) -> KeyRiskIndicator:
        self._kris[kri.kri_id] = kri
        return kri

    async def save_measurement(self, measurement: KRIMeasurement) -> KRIMeasurement:
        self._measurements[measurement.measurement_id] = measurement
        return measurement

    async def find_measurements_by_kri(self, kri_id: UUID) -> list[KRIMeasurement]:
        return sorted(
            [m for m in self._measurements.values() if m.kri_id == kri_id],
            key=lambda x: x.measurement_date
        )

    async def save_breach(self, breach: KRIThresholdBreach) -> KRIThresholdBreach:
        self._breaches[breach.breach_id] = breach
        return breach

    async def find_breach_by_id(self, breach_id: UUID) -> KRIThresholdBreach | None:
        return self._breaches.get(breach_id)

    async def find_breaches_by_kri(self, kri_id: UUID) -> list[KRIThresholdBreach]:
        return [b for b in self._breaches.values() if b.kri_id == kri_id]

    async def find_all_breaches(self) -> list[KRIThresholdBreach]:
        return list(self._breaches.values())

    async def save_target(self, target: KRITarget) -> KRITarget:
        self._targets[target.target_id] = target
        return target

    async def find_targets_by_kri(self, kri_id: UUID) -> list[KRITarget]:
        return [t for t in self._targets.values() if t.kri_id == kri_id]

    async def save_trend_analysis(self, analysis: KRITrendAnalysis) -> KRITrendAnalysis:
        self._trend_analyses[analysis.analysis_id] = analysis
        return analysis

    async def save_dashboard(self, dashboard: KRIDashboard) -> KRIDashboard:
        self._dashboards[dashboard.dashboard_id] = dashboard
        return dashboard

    async def save_report(self, report: KRIReport) -> KRIReport:
        self._reports[report.report_id] = report
        return report

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_kris": len(self._kris),
            "total_measurements": len(self._measurements),
            "total_breaches": len(self._breaches)
        }


kri_repository = KRIRepository()
