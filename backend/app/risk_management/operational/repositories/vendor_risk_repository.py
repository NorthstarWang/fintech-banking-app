"""Vendor Risk Repository - Data access layer for third-party risk"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.vendor_risk_models import (
    Vendor, VendorContract, VendorAssessment, VendorDueDiligence,
    VendorIncident, VendorPerformance, VendorRiskMetrics
)


class VendorRiskRepository:
    def __init__(self):
        self._vendors: Dict[UUID, Vendor] = {}
        self._contracts: Dict[UUID, VendorContract] = {}
        self._assessments: Dict[UUID, VendorAssessment] = {}
        self._due_diligences: Dict[UUID, VendorDueDiligence] = {}
        self._incidents: Dict[UUID, VendorIncident] = {}
        self._performances: Dict[UUID, VendorPerformance] = {}
        self._metrics: Dict[UUID, VendorRiskMetrics] = {}

    async def save_vendor(self, vendor: Vendor) -> Vendor:
        self._vendors[vendor.vendor_id] = vendor
        return vendor

    async def find_vendor_by_id(self, vendor_id: UUID) -> Optional[Vendor]:
        return self._vendors.get(vendor_id)

    async def find_vendor_by_code(self, vendor_code: str) -> Optional[Vendor]:
        for vendor in self._vendors.values():
            if vendor.vendor_code == vendor_code:
                return vendor
        return None

    async def find_all_vendors(self) -> List[Vendor]:
        return list(self._vendors.values())

    async def update_vendor(self, vendor: Vendor) -> Vendor:
        self._vendors[vendor.vendor_id] = vendor
        return vendor

    async def save_contract(self, contract: VendorContract) -> VendorContract:
        self._contracts[contract.contract_id] = contract
        return contract

    async def find_contracts_by_vendor(self, vendor_id: UUID) -> List[VendorContract]:
        return [c for c in self._contracts.values() if c.vendor_id == vendor_id]

    async def find_all_contracts(self) -> List[VendorContract]:
        return list(self._contracts.values())

    async def save_assessment(self, assessment: VendorAssessment) -> VendorAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    async def find_assessments_by_vendor(self, vendor_id: UUID) -> List[VendorAssessment]:
        return sorted(
            [a for a in self._assessments.values() if a.vendor_id == vendor_id],
            key=lambda x: x.assessment_date,
            reverse=True
        )

    async def save_due_diligence(self, dd: VendorDueDiligence) -> VendorDueDiligence:
        self._due_diligences[dd.due_diligence_id] = dd
        return dd

    async def find_due_diligence_by_id(self, dd_id: UUID) -> Optional[VendorDueDiligence]:
        return self._due_diligences.get(dd_id)

    async def find_due_diligence_by_vendor(self, vendor_id: UUID) -> List[VendorDueDiligence]:
        return [d for d in self._due_diligences.values() if d.vendor_id == vendor_id]

    async def save_incident(self, incident: VendorIncident) -> VendorIncident:
        self._incidents[incident.incident_id] = incident
        return incident

    async def find_incident_by_id(self, incident_id: UUID) -> Optional[VendorIncident]:
        return self._incidents.get(incident_id)

    async def find_incidents_by_vendor(self, vendor_id: UUID) -> List[VendorIncident]:
        return [i for i in self._incidents.values() if i.vendor_id == vendor_id]

    async def find_all_incidents(self) -> List[VendorIncident]:
        return list(self._incidents.values())

    async def save_performance(self, performance: VendorPerformance) -> VendorPerformance:
        self._performances[performance.performance_id] = performance
        return performance

    async def find_performance_by_vendor(self, vendor_id: UUID) -> List[VendorPerformance]:
        return sorted(
            [p for p in self._performances.values() if p.vendor_id == vendor_id],
            key=lambda x: x.review_date,
            reverse=True
        )

    async def find_all_performances(self) -> List[VendorPerformance]:
        return list(self._performances.values())

    async def save_metrics(self, metrics: VendorRiskMetrics) -> VendorRiskMetrics:
        self._metrics[metrics.metrics_id] = metrics
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        from decimal import Decimal
        total_spend = sum(v.annual_spend for v in self._vendors.values())
        return {
            "total_vendors": len(self._vendors),
            "total_contracts": len(self._contracts),
            "total_spend": str(total_spend)
        }


vendor_risk_repository = VendorRiskRepository()
