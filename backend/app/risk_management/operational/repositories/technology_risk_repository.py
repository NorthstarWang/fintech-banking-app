"""Technology Risk Repository - Data access layer for IT risk"""

from typing import Any
from uuid import UUID

from ..models.technology_risk_models import (
    AccessReview,
    ChangeRisk,
    ITAsset,
    PatchManagement,
    SecurityIncident,
    TechRiskAssessment,
    TechRiskMetrics,
    Vulnerability,
)


class TechnologyRiskRepository:
    def __init__(self):
        self._assets: dict[UUID, ITAsset] = {}
        self._vulnerabilities: dict[UUID, Vulnerability] = {}
        self._patches: dict[UUID, PatchManagement] = {}
        self._assessments: dict[UUID, TechRiskAssessment] = {}
        self._security_incidents: dict[UUID, SecurityIncident] = {}
        self._access_reviews: dict[UUID, AccessReview] = {}
        self._change_risks: dict[UUID, ChangeRisk] = {}
        self._metrics: dict[UUID, TechRiskMetrics] = {}

    async def save_asset(self, asset: ITAsset) -> ITAsset:
        self._assets[asset.asset_id] = asset
        return asset

    async def find_asset_by_id(self, asset_id: UUID) -> ITAsset | None:
        return self._assets.get(asset_id)

    async def find_asset_by_code(self, asset_code: str) -> ITAsset | None:
        for asset in self._assets.values():
            if asset.asset_code == asset_code:
                return asset
        return None

    async def find_all_assets(self) -> list[ITAsset]:
        return list(self._assets.values())

    async def update_asset(self, asset: ITAsset) -> ITAsset:
        self._assets[asset.asset_id] = asset
        return asset

    async def save_vulnerability(self, vuln: Vulnerability) -> Vulnerability:
        self._vulnerabilities[vuln.vulnerability_id] = vuln
        return vuln

    async def find_vulnerability_by_id(self, vuln_id: UUID) -> Vulnerability | None:
        return self._vulnerabilities.get(vuln_id)

    async def find_all_vulnerabilities(self) -> list[Vulnerability]:
        return list(self._vulnerabilities.values())

    async def find_vulnerabilities_by_asset(self, asset_id: UUID) -> list[Vulnerability]:
        return [v for v in self._vulnerabilities.values() if asset_id in v.affected_assets]

    async def save_patch(self, patch: PatchManagement) -> PatchManagement:
        self._patches[patch.patch_id] = patch
        return patch

    async def find_patch_by_id(self, patch_id: UUID) -> PatchManagement | None:
        return self._patches.get(patch_id)

    async def find_all_patches(self) -> list[PatchManagement]:
        return list(self._patches.values())

    async def save_assessment(self, assessment: TechRiskAssessment) -> TechRiskAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    async def find_assessments_by_asset(self, asset_id: UUID) -> list[TechRiskAssessment]:
        return sorted(
            [a for a in self._assessments.values() if a.asset_id == asset_id],
            key=lambda x: x.assessment_date,
            reverse=True
        )

    async def save_security_incident(self, incident: SecurityIncident) -> SecurityIncident:
        self._security_incidents[incident.incident_id] = incident
        return incident

    async def find_security_incident_by_id(self, incident_id: UUID) -> SecurityIncident | None:
        return self._security_incidents.get(incident_id)

    async def find_all_security_incidents(self) -> list[SecurityIncident]:
        return list(self._security_incidents.values())

    async def save_access_review(self, review: AccessReview) -> AccessReview:
        self._access_reviews[review.review_id] = review
        return review

    async def find_access_review_by_id(self, review_id: UUID) -> AccessReview | None:
        return self._access_reviews.get(review_id)

    async def find_all_access_reviews(self) -> list[AccessReview]:
        return list(self._access_reviews.values())

    async def save_change_risk(self, change: ChangeRisk) -> ChangeRisk:
        self._change_risks[change.change_id] = change
        return change

    async def find_all_change_risks(self) -> list[ChangeRisk]:
        return list(self._change_risks.values())

    async def save_metrics(self, metrics: TechRiskMetrics) -> TechRiskMetrics:
        self._metrics[metrics.metrics_id] = metrics
        return metrics

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_assets": len(self._assets),
            "total_vulnerabilities": len(self._vulnerabilities),
            "total_patches": len(self._patches),
            "total_incidents": len(self._security_incidents)
        }


technology_risk_repository = TechnologyRiskRepository()
