"""Data Governance Repository"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.data_governance_models import (
    DataDomain, DataOwnership, DataPolicy, DataStandard, BusinessGlossary,
    DataAccessRequest, DataPrivacyAssessment, GovernanceMetric
)


class DataGovernanceRepository:
    def __init__(self):
        self._domains: Dict[UUID, DataDomain] = {}
        self._ownerships: Dict[UUID, DataOwnership] = {}
        self._policies: Dict[UUID, DataPolicy] = {}
        self._standards: Dict[UUID, DataStandard] = {}
        self._glossary_terms: Dict[UUID, BusinessGlossary] = {}
        self._access_requests: Dict[UUID, DataAccessRequest] = {}
        self._privacy_assessments: Dict[UUID, DataPrivacyAssessment] = {}
        self._metrics: Dict[UUID, GovernanceMetric] = {}

    async def save_domain(self, domain: DataDomain) -> DataDomain:
        self._domains[domain.domain_id] = domain
        return domain

    async def find_domain_by_id(self, domain_id: UUID) -> Optional[DataDomain]:
        return self._domains.get(domain_id)

    async def find_all_domains(self) -> List[DataDomain]:
        return list(self._domains.values())

    async def find_domain_by_code(self, domain_code: str) -> Optional[DataDomain]:
        for domain in self._domains.values():
            if domain.domain_code == domain_code:
                return domain
        return None

    async def find_active_domains(self) -> List[DataDomain]:
        return [d for d in self._domains.values() if d.is_active]

    async def delete_domain(self, domain_id: UUID) -> bool:
        if domain_id in self._domains:
            del self._domains[domain_id]
            return True
        return False

    async def save_ownership(self, ownership: DataOwnership) -> DataOwnership:
        self._ownerships[ownership.ownership_id] = ownership
        return ownership

    async def find_ownership_by_id(self, ownership_id: UUID) -> Optional[DataOwnership]:
        return self._ownerships.get(ownership_id)

    async def find_all_ownerships(self) -> List[DataOwnership]:
        return list(self._ownerships.values())

    async def find_ownerships_by_owner(self, business_owner: str) -> List[DataOwnership]:
        return [o for o in self._ownerships.values() if o.business_owner == business_owner]

    async def find_ownership_by_asset(self, asset_id: UUID) -> Optional[DataOwnership]:
        for ownership in self._ownerships.values():
            if ownership.asset_id == asset_id:
                return ownership
        return None

    async def save_policy(self, policy: DataPolicy) -> DataPolicy:
        self._policies[policy.policy_id] = policy
        return policy

    async def find_policy_by_id(self, policy_id: UUID) -> Optional[DataPolicy]:
        return self._policies.get(policy_id)

    async def find_all_policies(self) -> List[DataPolicy]:
        return list(self._policies.values())

    async def find_policies_by_type(self, policy_type: str) -> List[DataPolicy]:
        return [p for p in self._policies.values() if p.policy_type == policy_type]

    async def find_active_policies(self) -> List[DataPolicy]:
        return [p for p in self._policies.values() if p.status == "active"]

    async def find_policy_by_code(self, policy_code: str) -> Optional[DataPolicy]:
        for policy in self._policies.values():
            if policy.policy_code == policy_code:
                return policy
        return None

    async def save_standard(self, standard: DataStandard) -> DataStandard:
        self._standards[standard.standard_id] = standard
        return standard

    async def find_standard_by_id(self, standard_id: UUID) -> Optional[DataStandard]:
        return self._standards.get(standard_id)

    async def find_all_standards(self) -> List[DataStandard]:
        return list(self._standards.values())

    async def find_standards_by_type(self, standard_type: str) -> List[DataStandard]:
        return [s for s in self._standards.values() if s.standard_type == standard_type]

    async def find_active_standards(self) -> List[DataStandard]:
        return [s for s in self._standards.values() if s.status == "active"]

    async def save_glossary_term(self, term: BusinessGlossary) -> BusinessGlossary:
        self._glossary_terms[term.term_id] = term
        return term

    async def find_glossary_term_by_id(self, term_id: UUID) -> Optional[BusinessGlossary]:
        return self._glossary_terms.get(term_id)

    async def find_all_glossary_terms(self) -> List[BusinessGlossary]:
        return list(self._glossary_terms.values())

    async def find_glossary_terms_by_domain(self, domain_id: UUID) -> List[BusinessGlossary]:
        return [t for t in self._glossary_terms.values() if t.domain_id == domain_id]

    async def search_glossary(self, query: str) -> List[BusinessGlossary]:
        query_lower = query.lower()
        return [
            t for t in self._glossary_terms.values()
            if query_lower in t.term_name.lower() or query_lower in t.term_definition.lower()
        ]

    async def save_access_request(self, request: DataAccessRequest) -> DataAccessRequest:
        self._access_requests[request.request_id] = request
        return request

    async def find_access_request_by_id(self, request_id: UUID) -> Optional[DataAccessRequest]:
        return self._access_requests.get(request_id)

    async def find_all_access_requests(self) -> List[DataAccessRequest]:
        return list(self._access_requests.values())

    async def find_pending_access_requests(self) -> List[DataAccessRequest]:
        return [r for r in self._access_requests.values() if r.status == "pending"]

    async def find_access_requests_by_requestor(self, requestor: str) -> List[DataAccessRequest]:
        return [r for r in self._access_requests.values() if r.requestor == requestor]

    async def find_access_requests_by_asset(self, asset_id: UUID) -> List[DataAccessRequest]:
        return [r for r in self._access_requests.values() if r.asset_id == asset_id]

    async def save_privacy_assessment(self, assessment: DataPrivacyAssessment) -> DataPrivacyAssessment:
        self._privacy_assessments[assessment.assessment_id] = assessment
        return assessment

    async def find_privacy_assessment_by_id(self, assessment_id: UUID) -> Optional[DataPrivacyAssessment]:
        return self._privacy_assessments.get(assessment_id)

    async def find_all_privacy_assessments(self) -> List[DataPrivacyAssessment]:
        return list(self._privacy_assessments.values())

    async def find_privacy_assessments_by_risk_level(self, risk_level: str) -> List[DataPrivacyAssessment]:
        return [a for a in self._privacy_assessments.values() if a.risk_level == risk_level]

    async def find_pii_containing_assets(self) -> List[DataPrivacyAssessment]:
        return [a for a in self._privacy_assessments.values() if a.contains_pii]

    async def save_metric(self, metric: GovernanceMetric) -> GovernanceMetric:
        self._metrics[metric.metric_id] = metric
        return metric

    async def find_metric_by_id(self, metric_id: UUID) -> Optional[GovernanceMetric]:
        return self._metrics.get(metric_id)

    async def find_all_metrics(self) -> List[GovernanceMetric]:
        return list(self._metrics.values())

    async def find_metrics_by_type(self, metric_type: str) -> List[GovernanceMetric]:
        return [m for m in self._metrics.values() if m.metric_type == metric_type]

    async def find_metrics_by_status(self, status: str) -> List[GovernanceMetric]:
        return [m for m in self._metrics.values() if m.status == status]

    async def get_statistics(self) -> Dict[str, Any]:
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
