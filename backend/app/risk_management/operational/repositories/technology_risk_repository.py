"""Technology Risk Repository - Data access layer for IT risk"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.technology_risk_models import (
    ITAsset, Vulnerability, PatchManagement, TechRiskAssessment,
    SecurityIncident, AccessReview, ChangeRisk, TechRiskMetrics
)


class TechnologyRiskRepository:
    def __init__(self):
        self._assets: Dict[UUID, ITAsset] = {}
        self._vulnerabilities: Dict[UUID, Vulnerability] = {}
        self._patches: Dict[UUID, PatchManagement] = {}
        self._assessments: Dict[UUID, TechRiskAssessment] = {}
        self._security_incidents: Dict[UUID, SecurityIncident] = {}
        self._access_reviews: Dict[UUID, AccessReview] = {}
        self._change_risks: Dict[UUID, ChangeRisk] = {}
        self._metrics: Dict[UUID, TechRiskMetrics] = {}

    async def save_asset(self, asset: ITAsset) -> ITAsset:
        self._assets[asset.asset_id] = asset
        return asset

    async def find_asset_by_id(self, asset_id: UUID) -> Optional[ITAsset]:
        return self._assets.get(asset_id)

    async def find_asset_by_code(self, asset_code: str) -> Optional[ITAsset]:
        for asset in self._assets.values():
            if asset.asset_code == asset_code:
                return asset
        return None

    async def find_all_assets(self) -> List[ITAsset]:
        return list(self._assets.values())

    async def update_asset(self, asset: ITAsset) -> ITAsset:
        self._assets[asset.asset_id] = asset
        return asset

    async def save_vulnerability(self, vuln: Vulnerability) -> Vulnerability:
        self._vulnerabilities[vuln.vulnerability_id] = vuln
        return vuln

    async def find_vulnerability_by_id(self, vuln_id: UUID) -> Optional[Vulnerability]:
        return self._vulnerabilities.get(vuln_id)

    async def find_all_vulnerabilities(self) -> List[Vulnerability]:
        return list(self._vulnerabilities.values())

    async def find_vulnerabilities_by_asset(self, asset_id: UUID) -> List[Vulnerability]:
        return [v for v in self._vulnerabilities.values() if asset_id in v.affected_assets]

    async def save_patch(self, patch: PatchManagement) -> PatchManagement:
        self._patches[patch.patch_id] = patch
        return patch

    async def find_patch_by_id(self, patch_id: UUID) -> Optional[PatchManagement]:
        return self._patches.get(patch_id)

    async def find_all_patches(self) -> List[PatchManagement]:
        return list(self._patches.values())

    async def save_assessment(self, assessment: TechRiskAssessment) -> TechRiskAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    async def find_assessments_by_asset(self, asset_id: UUID) -> List[TechRiskAssessment]:
        return sorted(
            [a for a in self._assessments.values() if a.asset_id == asset_id],
            key=lambda x: x.assessment_date,
            reverse=True
        )

    async def save_security_incident(self, incident: SecurityIncident) -> SecurityIncident:
        self._security_incidents[incident.incident_id] = incident
        return incident

    async def find_security_incident_by_id(self, incident_id: UUID) -> Optional[SecurityIncident]:
        return self._security_incidents.get(incident_id)

    async def find_all_security_incidents(self) -> List[SecurityIncident]:
        return list(self._security_incidents.values())

    async def save_access_review(self, review: AccessReview) -> AccessReview:
        self._access_reviews[review.review_id] = review
        return review

    async def find_access_review_by_id(self, review_id: UUID) -> Optional[AccessReview]:
        return self._access_reviews.get(review_id)

    async def find_all_access_reviews(self) -> List[AccessReview]:
        return list(self._access_reviews.values())

    async def save_change_risk(self, change: ChangeRisk) -> ChangeRisk:
        self._change_risks[change.change_id] = change
        return change

    async def find_all_change_risks(self) -> List[ChangeRisk]:
        return list(self._change_risks.values())

    async def save_metrics(self, metrics: TechRiskMetrics) -> TechRiskMetrics:
        self._metrics[metrics.metrics_id] = metrics
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_assets": len(self._assets),
            "total_vulnerabilities": len(self._vulnerabilities),
            "total_patches": len(self._patches),
            "total_incidents": len(self._security_incidents)
        }


technology_risk_repository = TechnologyRiskRepository()
