"""Policy Service - Business logic for policy management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.policy_models import (
    Policy, PolicyVersion, PolicyException, PolicyAttestation, PolicyReview,
    Procedure, PolicyStatus, PolicyCategory
)
from ..repositories.policy_repository import policy_repository


class PolicyService:
    def __init__(self):
        self.repository = policy_repository
        self._exception_counter = 0

    async def create_policy(
        self, policy_code: str, policy_name: str, policy_category: PolicyCategory,
        description: str, purpose: str, scope: str, policy_statement: str,
        owner: str, approver: str, created_by: str
    ) -> Policy:
        policy = Policy(
            policy_code=policy_code, policy_name=policy_name, policy_category=policy_category,
            version="1.0", description=description, purpose=purpose, scope=scope,
            policy_statement=policy_statement, owner=owner, approver=approver,
            effective_date=date.today(), review_date=date.today(),
            next_review_date=date(date.today().year + 1, date.today().month, date.today().day),
            created_by=created_by
        )
        await self.repository.save_policy(policy)
        return policy

    async def approve_policy(self, policy_id: UUID) -> Optional[Policy]:
        policy = await self.repository.find_policy_by_id(policy_id)
        if policy:
            policy.status = PolicyStatus.APPROVED
        return policy

    async def activate_policy(self, policy_id: UUID) -> Optional[Policy]:
        policy = await self.repository.find_policy_by_id(policy_id)
        if policy and policy.status == PolicyStatus.APPROVED:
            policy.status = PolicyStatus.ACTIVE
            policy.effective_date = date.today()
        return policy

    async def create_version(
        self, policy_id: UUID, version_number: str, change_summary: str,
        changes_made: List[str], changed_by: str
    ) -> PolicyVersion:
        policy = await self.repository.find_policy_by_id(policy_id)
        prior_version = policy.version if policy else None

        version = PolicyVersion(
            policy_id=policy_id, version_number=version_number, change_summary=change_summary,
            changes_made=changes_made, changed_by=changed_by, change_date=date.today(),
            effective_date=date.today(), supersedes_version=prior_version
        )
        await self.repository.save_version(version)

        if policy:
            policy.version = version_number
            policy.status = PolicyStatus.UNDER_REVIEW

        return version

    async def request_exception(
        self, policy_id: UUID, requestor: str, business_unit: str, exception_type: str,
        description: str, justification: str, risk_assessment: str,
        compensating_controls: List[str], duration: str, expiry_date: date
    ) -> PolicyException:
        self._exception_counter += 1
        exception = PolicyException(
            policy_id=policy_id, exception_reference=f"EXC-{self._exception_counter:05d}",
            requestor=requestor, request_date=date.today(), business_unit=business_unit,
            exception_type=exception_type, description=description, justification=justification,
            risk_assessment=risk_assessment, compensating_controls=compensating_controls,
            duration=duration, expiry_date=expiry_date
        )
        await self.repository.save_exception(exception)
        return exception

    async def approve_exception(
        self, exception_id: UUID, approved_by: str
    ) -> Optional[PolicyException]:
        exception = await self.repository.find_exception_by_id(exception_id)
        if exception:
            exception.approved_by = approved_by
            exception.approval_date = date.today()
            exception.status = "approved"
        return exception

    async def record_attestation(
        self, policy_id: UUID, attestation_period: str, employee_id: str,
        employee_name: str, department: str, acknowledged: bool,
        understood: bool, compliant: bool
    ) -> PolicyAttestation:
        attestation = PolicyAttestation(
            policy_id=policy_id, attestation_period=attestation_period,
            employee_id=employee_id, employee_name=employee_name, department=department,
            attestation_date=date.today(), acknowledged=acknowledged,
            understood=understood, compliant=compliant
        )
        await self.repository.save_attestation(attestation)
        return attestation

    async def review_policy(
        self, policy_id: UUID, reviewer: str, review_type: str,
        current_relevance: str, regulatory_alignment: str, operational_effectiveness: str,
        gaps_identified: List[str], recommendations: List[str], changes_required: bool
    ) -> PolicyReview:
        review = PolicyReview(
            policy_id=policy_id, review_date=date.today(), reviewer=reviewer,
            review_type=review_type, current_relevance=current_relevance,
            regulatory_alignment=regulatory_alignment, operational_effectiveness=operational_effectiveness,
            gaps_identified=gaps_identified, recommendations=recommendations,
            changes_required=changes_required
        )
        await self.repository.save_review(review)

        policy = await self.repository.find_policy_by_id(policy_id)
        if policy:
            policy.review_date = date.today()
            policy.next_review_date = date(date.today().year + 1, date.today().month, date.today().day)

        return review

    async def create_procedure(
        self, policy_id: UUID, procedure_code: str, procedure_name: str,
        description: str, steps: List[Dict[str, Any]], responsible_role: str,
        owner: str
    ) -> Procedure:
        procedure = Procedure(
            policy_id=policy_id, procedure_code=procedure_code, procedure_name=procedure_name,
            version="1.0", description=description, steps=steps,
            responsible_role=responsible_role, owner=owner, effective_date=date.today()
        )
        await self.repository.save_procedure(procedure)
        return procedure

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


policy_service = PolicyService()
