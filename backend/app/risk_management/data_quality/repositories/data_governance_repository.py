"""Data Governance Repository"""

from typing import Any
from uuid import UUID

from ..models.data_governance_models import (
    BusinessGlossary,
    DataAccessRequest,
    DataDomain,
    DataOwnership,
    DataPolicy,
    DataPrivacyAssessment,
    DataStandard,
    GovernanceMetric,
)


class DataGovernanceRepository:
    def __init__(self):
        self._domains: dict[UUID, DataDomain] = {}
        self._ownerships: dict[UUID, DataOwnership] = {}
        self._policies: dict[UUID, DataPolicy] = {}
        self._standards: dict[UUID, DataStandard] = {}
        self._glossary_terms: dict[UUID, BusinessGlossary] = {}
        self._access_requests: dict[UUID, DataAccessRequest] = {}
        self._privacy_assessments: dict[UUID, DataPrivacyAssessment] = {}
        self._metrics: dict[UUID, GovernanceMetric] = {}

    async def save_domain(self, domain: DataDomain) -> DataDomain:
        self._domains[domain.domain_id] = domain
        return domain

    async def find_domain_by_id(self, domain_id: UUID) -> DataDomain | None:
        return self._domains.get(domain_id)

    async def find_all_domains(self) -> list[DataDomain]:
        return list(self._domains.values())

    async def find_domain_by_code(self, domain_code: str) -> DataDomain | None:
        for domain in self._domains.values():
            if domain.domain_code == domain_code:
                return domain
        return None

    async def find_active_domains(self) -> list[DataDomain]:
        return [d for d in self._domains.values() if d.is_active]

    async def delete_domain(self, domain_id: UUID) -> bool:
        if domain_id in self._domains:
            del self._domains[domain_id]
            return True
        return False

    async def save_ownership(self, ownership: DataOwnership) -> DataOwnership:
        self._ownerships[ownership.ownership_id] = ownership
        return ownership

    async def find_ownership_by_id(self, ownership_id: UUID) -> DataOwnership | None:
        return self._ownerships.get(ownership_id)

    async def find_all_ownerships(self) -> list[DataOwnership]:
        return list(self._ownerships.values())

    async def find_ownerships_by_owner(self, business_owner: str) -> list[DataOwnership]:
        return [o for o in self._ownerships.values() if o.business_owner == business_owner]

    async def find_ownership_by_asset(self, asset_id: UUID) -> DataOwnership | None:
        for ownership in self._ownerships.values():
            if ownership.asset_id == asset_id:
                return ownership
        return None

    async def save_policy(self, policy: DataPolicy) -> DataPolicy:
        self._policies[policy.policy_id] = policy
        return policy

    async def find_policy_by_id(self, policy_id: UUID) -> DataPolicy | None:
        return self._policies.get(policy_id)

    async def find_all_policies(self) -> list[DataPolicy]:
        return list(self._policies.values())

    async def find_policies_by_type(self, policy_type: str) -> list[DataPolicy]:
        return [p for p in self._policies.values() if p.policy_type == policy_type]

    async def find_active_policies(self) -> list[DataPolicy]:
        return [p for p in self._policies.values() if p.status == "active"]

    async def find_policy_by_code(self, policy_code: str) -> DataPolicy | None:
        for policy in self._policies.values():
            if policy.policy_code == policy_code:
                return policy
        return None

    async def save_standard(self, standard: DataStandard) -> DataStandard:
        self._standards[standard.standard_id] = standard
        return standard

    async def find_standard_by_id(self, standard_id: UUID) -> DataStandard | None:
        return self._standards.get(standard_id)

    async def find_all_standards(self) -> list[DataStandard]:
        return list(self._standards.values())

    async def find_standards_by_type(self, standard_type: str) -> list[DataStandard]:
        return [s for s in self._standards.values() if s.standard_type == standard_type]

    async def find_active_standards(self) -> list[DataStandard]:
        return [s for s in self._standards.values() if s.status == "active"]

    async def save_glossary_term(self, term: BusinessGlossary) -> BusinessGlossary:
        self._glossary_terms[term.term_id] = term
        return term

    async def find_glossary_term_by_id(self, term_id: UUID) -> BusinessGlossary | None:
        return self._glossary_terms.get(term_id)

    async def find_all_glossary_terms(self) -> list[BusinessGlossary]:
        return list(self._glossary_terms.values())

    async def find_glossary_terms_by_domain(self, domain_id: UUID) -> list[BusinessGlossary]:
        return [t for t in self._glossary_terms.values() if t.domain_id == domain_id]

    async def search_glossary(self, query: str) -> list[BusinessGlossary]:
        query_lower = query.lower()
        return [
            t for t in self._glossary_terms.values()
            if query_lower in t.term_name.lower() or query_lower in t.term_definition.lower()
        ]

    async def save_access_request(self, request: DataAccessRequest) -> DataAccessRequest:
        self._access_requests[request.request_id] = request
        return request

    async def find_access_request_by_id(self, request_id: UUID) -> DataAccessRequest | None:
        return self._access_requests.get(request_id)

    async def find_all_access_requests(self) -> list[DataAccessRequest]:
        return list(self._access_requests.values())

    async def find_pending_access_requests(self) -> list[DataAccessRequest]:
        return [r for r in self._access_requests.values() if r.status == "pending"]

    async def find_access_requests_by_requestor(self, requestor: str) -> list[DataAccessRequest]:
        return [r for r in self._access_requests.values() if r.requestor == requestor]

    async def find_access_requests_by_asset(self, asset_id: UUID) -> list[DataAccessRequest]:
        return [r for r in self._access_requests.values() if r.asset_id == asset_id]

    async def save_privacy_assessment(self, assessment: DataPrivacyAssessment) -> DataPrivacyAssessment:
        self._privacy_assessments[assessment.assessment_id] = assessment
        return assessment

    async def find_privacy_assessment_by_id(self, assessment_id: UUID) -> DataPrivacyAssessment | None:
        return self._privacy_assessments.get(assessment_id)

    async def find_all_privacy_assessments(self) -> list[DataPrivacyAssessment]:
        return list(self._privacy_assessments.values())

    async def find_privacy_assessments_by_risk_level(self, risk_level: str) -> list[DataPrivacyAssessment]:
        return [a for a in self._privacy_assessments.values() if a.risk_level == risk_level]

    async def find_pii_containing_assets(self) -> list[DataPrivacyAssessment]:
        return [a for a in self._privacy_assessments.values() if a.contains_pii]

    async def save_metric(self, metric: GovernanceMetric) -> GovernanceMetric:
        self._metrics[metric.metric_id] = metric
        return metric

    async def find_metric_by_id(self, metric_id: UUID) -> GovernanceMetric | None:
        return self._metrics.get(metric_id)

    async def find_all_metrics(self) -> list[GovernanceMetric]:
        return list(self._metrics.values())

    async def find_metrics_by_type(self, metric_type: str) -> list[GovernanceMetric]:
        return [m for m in self._metrics.values() if m.metric_type == metric_type]

    async def find_metrics_by_status(self, status: str) -> list[GovernanceMetric]:
        return [m for m in self._metrics.values() if m.status == status]

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_domains": len(self._domains),
            "active_domains": len([d for d in self._domains.values() if d.is_active]),
            "total_ownerships": len(self._ownerships),
            "total_policies": len(self._policies),
            "active_policies": len([p for p in self._policies.values() if p.status == "active"]),
            "total_standards": len(self._standards),
            "total_glossary_terms": len(self._glossary_terms),
            "pending_access_requests": len([r for r in self._access_requests.values() if r.status == "pending"]),
            "total_privacy_assessments": len(self._privacy_assessments),
            "high_risk_assessments": len([a for a in self._privacy_assessments.values() if a.risk_level == "high"]),
            "total_metrics": len(self._metrics),
        }


data_governance_repository = DataGovernanceRepository()
