"""Policy Repository - Data access for policy management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.policy_models import (
    Policy, PolicyVersion, PolicyException, PolicyAttestation, PolicyReview,
    Procedure, PolicyStatus
)


class PolicyRepository:
    def __init__(self):
        self._policies: Dict[UUID, Policy] = {}
        self._versions: Dict[UUID, PolicyVersion] = {}
        self._exceptions: Dict[UUID, PolicyException] = {}
        self._attestations: Dict[UUID, PolicyAttestation] = {}
        self._reviews: Dict[UUID, PolicyReview] = {}
        self._procedures: Dict[UUID, Procedure] = {}

    async def save_policy(self, policy: Policy) -> None:
        self._policies[policy.policy_id] = policy

    async def find_policy_by_id(self, policy_id: UUID) -> Optional[Policy]:
        return self._policies.get(policy_id)

    async def find_all_policies(self) -> List[Policy]:
        return list(self._policies.values())

    async def find_active_policies(self) -> List[Policy]:
        return [p for p in self._policies.values() if p.status == PolicyStatus.ACTIVE]

    async def find_policies_by_category(self, category: str) -> List[Policy]:
        return [p for p in self._policies.values() if p.policy_category.value == category]

    async def save_version(self, version: PolicyVersion) -> None:
        self._versions[version.version_id] = version

    async def find_version_by_id(self, version_id: UUID) -> Optional[PolicyVersion]:
        return self._versions.get(version_id)

    async def find_versions_by_policy(self, policy_id: UUID) -> List[PolicyVersion]:
        return [v for v in self._versions.values() if v.policy_id == policy_id]

    async def save_exception(self, exception: PolicyException) -> None:
        self._exceptions[exception.exception_id] = exception

    async def find_exception_by_id(self, exception_id: UUID) -> Optional[PolicyException]:
        return self._exceptions.get(exception_id)

    async def find_all_exceptions(self) -> List[PolicyException]:
        return list(self._exceptions.values())

    async def find_active_exceptions(self) -> List[PolicyException]:
        return [e for e in self._exceptions.values() if e.status == "approved"]

    async def save_attestation(self, attestation: PolicyAttestation) -> None:
        self._attestations[attestation.attestation_id] = attestation

    async def find_attestation_by_id(self, attestation_id: UUID) -> Optional[PolicyAttestation]:
        return self._attestations.get(attestation_id)

    async def find_attestations_by_policy(self, policy_id: UUID) -> List[PolicyAttestation]:
        return [a for a in self._attestations.values() if a.policy_id == policy_id]

    async def save_review(self, review: PolicyReview) -> None:
        self._reviews[review.review_id] = review

    async def find_review_by_id(self, review_id: UUID) -> Optional[PolicyReview]:
        return self._reviews.get(review_id)

    async def find_reviews_by_policy(self, policy_id: UUID) -> List[PolicyReview]:
        return [r for r in self._reviews.values() if r.policy_id == policy_id]

    async def save_procedure(self, procedure: Procedure) -> None:
        self._procedures[procedure.procedure_id] = procedure

    async def find_procedure_by_id(self, procedure_id: UUID) -> Optional[Procedure]:
        return self._procedures.get(procedure_id)

    async def find_procedures_by_policy(self, policy_id: UUID) -> List[Procedure]:
        return [p for p in self._procedures.values() if p.policy_id == policy_id]

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_policies": len(self._policies),
            "active_policies": len([p for p in self._policies.values() if p.status == PolicyStatus.ACTIVE]),
            "total_versions": len(self._versions),
            "total_exceptions": len(self._exceptions),
            "active_exceptions": len([e for e in self._exceptions.values() if e.status == "approved"]),
            "total_attestations": len(self._attestations),
            "total_reviews": len(self._reviews),
            "total_procedures": len(self._procedures),
        }


policy_repository = PolicyRepository()
