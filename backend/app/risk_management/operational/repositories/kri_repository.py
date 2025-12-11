"""KRI Repository - Data access layer for Key Risk Indicators"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.kri_models import (
    KeyRiskIndicator, KRIMeasurement, KRIThresholdBreach,
    KRITarget, KRITrendAnalysis, KRIDashboard, KRIReport
)


class KRIRepository:
    def __init__(self):
        self._kris: Dict[UUID, KeyRiskIndicator] = {}
        self._measurements: Dict[UUID, KRIMeasurement] = {}
        self._breaches: Dict[UUID, KRIThresholdBreach] = {}
        self._targets: Dict[UUID, KRITarget] = {}
        self._trend_analyses: Dict[UUID, KRITrendAnalysis] = {}
        self._dashboards: Dict[UUID, KRIDashboard] = {}
        self._reports: Dict[UUID, KRIReport] = {}

    async def save_kri(self, kri: KeyRiskIndicator) -> KeyRiskIndicator:
        self._kris[kri.kri_id] = kri
        return kri

    async def find_kri_by_id(self, kri_id: UUID) -> Optional[KeyRiskIndicator]:
        return self._kris.get(kri_id)

    async def find_kri_by_code(self, kri_code: str) -> Optional[KeyRiskIndicator]:
        for kri in self._kris.values():
            if kri.kri_code == kri_code:
                return kri
        return None

    async def find_all_kris(self) -> List[KeyRiskIndicator]:
        return list(self._kris.values())

    async def update_kri(self, kri: KeyRiskIndicator) -> KeyRiskIndicator:
        self._kris[kri.kri_id] = kri
        return kri

    async def save_measurement(self, measurement: KRIMeasurement) -> KRIMeasurement:
        self._measurements[measurement.measurement_id] = measurement
        return measurement

    async def find_measurements_by_kri(self, kri_id: UUID) -> List[KRIMeasurement]:
        return sorted(
            [m for m in self._measurements.values() if m.kri_id == kri_id],
            key=lambda x: x.measurement_date
        )

    async def save_breach(self, breach: KRIThresholdBreach) -> KRIThresholdBreach:
        self._breaches[breach.breach_id] = breach
        return breach

    async def find_breach_by_id(self, breach_id: UUID) -> Optional[KRIThresholdBreach]:
        return self._breaches.get(breach_id)

    async def find_breaches_by_kri(self, kri_id: UUID) -> List[KRIThresholdBreach]:
        return [b for b in self._breaches.values() if b.kri_id == kri_id]

    async def find_all_breaches(self) -> List[KRIThresholdBreach]:
        return list(self._breaches.values())

    async def save_target(self, target: KRITarget) -> KRITarget:
        self._targets[target.target_id] = target
        return target

    async def find_targets_by_kri(self, kri_id: UUID) -> List[KRITarget]:
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

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_kris": len(self._kris),
            "total_measurements": len(self._measurements),
            "total_breaches": len(self._breaches)
        }


kri_repository = KRIRepository()
