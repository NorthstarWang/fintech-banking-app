"""Data Governance Service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.data_governance_models import (
    DataDomain, DataOwnership, DataPolicy, DataStandard, BusinessGlossary,
    DataAccessRequest, DataPrivacyAssessment, GovernanceMetric
)
from ..repositories.data_governance_repository import data_governance_repository


class DataGovernanceService:
    def __init__(self):
        self.repository = data_governance_repository
        self._request_counter = 0

    async def create_domain(
        self, domain_name: str, domain_code: str, description: str,
        business_owner: str, data_steward: str, technical_owner: str
    ) -> DataDomain:
        domain = DataDomain(
            domain_name=domain_name, domain_code=domain_code, description=description,
            business_owner=business_owner, data_steward=data_steward,
            technical_owner=technical_owner
        )
        await self.repository.save_domain(domain)
        return domain

    async def assign_ownership(
        self, asset_id: UUID, asset_name: str, business_owner: str,
        data_steward: str, technical_owner: str, responsibilities: Dict[str, List[str]]
    ) -> DataOwnership:
        ownership = DataOwnership(
            asset_id=asset_id, asset_name=asset_name, business_owner=business_owner,
            data_steward=data_steward, technical_owner=technical_owner,
            effective_date=date.today(), responsibilities=responsibilities
        )
        await self.repository.save_ownership(ownership)
        return ownership

    async def create_policy(
        self, policy_code: str, policy_name: str, policy_type: str,
        description: str, scope: str, requirements: List[str],
        owner: str, approver: str
    ) -> DataPolicy:
        policy = DataPolicy(
            policy_code=policy_code, policy_name=policy_name, policy_type=policy_type,
            description=description, scope=scope, requirements=requirements,
            owner=owner, approver=approver, effective_date=date.today(),
            review_date=date(date.today().year + 1, date.today().month, date.today().day)
        )
        await self.repository.save_policy(policy)
        return policy

    async def create_standard(
        self, standard_code: str, standard_name: str, standard_type: str,
        description: str, rules: List[Dict[str, Any]], owner: str,
        domain_applicability: List[str]
    ) -> DataStandard:
        standard = DataStandard(
            standard_code=standard_code, standard_name=standard_name,
            standard_type=standard_type, description=description, rules=rules,
            owner=owner, domain_applicability=domain_applicability,
            effective_date=date.today()
        )
        await self.repository.save_standard(standard)
        return standard

    async def add_glossary_term(
        self, term_name: str, term_definition: str, domain_id: UUID,
        owner: str, steward: str, synonyms: List[str] = None
    ) -> BusinessGlossary:
        term = BusinessGlossary(
            term_name=term_name, term_definition=term_definition, domain_id=domain_id,
            owner=owner, steward=steward, synonyms=synonyms or []
        )
        await self.repository.save_glossary_term(term)
        return term

    async def submit_access_request(
        self, requestor: str, requestor_department: str, asset_id: UUID,
        asset_name: str, access_type: str, purpose: str, duration: str,
        justification: str
    ) -> DataAccessRequest:
        self._request_counter += 1
        request = DataAccessRequest(
            requestor=requestor, requestor_department=requestor_department,
            asset_id=asset_id, asset_name=asset_name, access_type=access_type,
            purpose=purpose, duration=duration, justification=justification
        )
        await self.repository.save_access_request(request)
        return request

    async def approve_access_request(
        self, request_id: UUID, approver: str, expiry_date: date
    ) -> Optional[DataAccessRequest]:
        request = await self.repository.find_access_request_by_id(request_id)
        if request:
            request.status = "approved"
            request.approver = approver
            request.approval_date = datetime.utcnow()
            request.expiry_date = expiry_date
        return request

    async def conduct_privacy_assessment(
        self, asset_id: UUID, asset_name: str, assessor: str,
        contains_pii: bool, pii_categories: List[str], data_subjects: List[str],
        processing_purposes: List[str], security_controls: List[str]
    ) -> DataPrivacyAssessment:
        risk_level = "high" if contains_pii and len(pii_categories) > 3 else "medium" if contains_pii else "low"

        assessment = DataPrivacyAssessment(
            asset_id=asset_id, asset_name=asset_name, assessment_date=date.today(),
            assessor=assessor, contains_pii=contains_pii, pii_categories=pii_categories,
            data_subjects=data_subjects, processing_purposes=processing_purposes,
            security_controls=security_controls, risk_level=risk_level
        )
        await self.repository.save_privacy_assessment(assessment)
        return assessment

    async def record_metric(
        self, metric_name: str, metric_type: str, current_value: float,
        target_value: float, threshold_value: float, domain_id: UUID = None
    ) -> GovernanceMetric:
        status = "green" if current_value >= target_value else "yellow" if current_value >= threshold_value else "red"

        metric = GovernanceMetric(
            metric_date=date.today(), domain_id=domain_id, metric_name=metric_name,
            metric_type=metric_type, current_value=current_value,
            target_value=target_value, threshold_value=threshold_value, status=status
        )
        await self.repository.save_metric(metric)
        return metric

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


data_governance_service = DataGovernanceService()
