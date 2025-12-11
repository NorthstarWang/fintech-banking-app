"""Data Governance Routes"""

from typing import List, Dict, Any
from uuid import UUID
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.data_governance_service import data_governance_service

router = APIRouter(prefix="/data-governance", tags=["Data Governance"])


class CreateDomainRequest(BaseModel):
    domain_name: str
    domain_code: str
    description: str
    business_owner: str
    data_steward: str
    technical_owner: str


class AssignOwnershipRequest(BaseModel):
    asset_id: UUID
    asset_name: str
    business_owner: str
    data_steward: str
    technical_owner: str
    responsibilities: Dict[str, List[str]]


class CreatePolicyRequest(BaseModel):
    policy_code: str
    policy_name: str
    policy_type: str
    description: str
    scope: str
    requirements: List[str]
    owner: str
    approver: str


class CreateStandardRequest(BaseModel):
    standard_code: str
    standard_name: str
    standard_type: str
    description: str
    rules: List[Dict[str, Any]]
    owner: str
    domain_applicability: List[str]


class AddGlossaryTermRequest(BaseModel):
    term_name: str
    term_definition: str
    domain_id: UUID
    owner: str
    steward: str
    synonyms: List[str] = []


class SubmitAccessRequestRequest(BaseModel):
    requestor: str
    requestor_department: str
    asset_id: UUID
    asset_name: str
    access_type: str
    purpose: str
    duration: str
    justification: str


class ConductPrivacyAssessmentRequest(BaseModel):
    asset_id: UUID
    asset_name: str
    assessor: str
    contains_pii: bool
    pii_categories: List[str]
    data_subjects: List[str]
    processing_purposes: List[str]
    security_controls: List[str]


class RecordMetricRequest(BaseModel):
    metric_name: str
    metric_type: str
    current_value: float
    target_value: float
    threshold_value: float
    domain_id: UUID = None


@router.post("/domains")
async def create_domain(request: CreateDomainRequest):
    domain = await data_governance_service.create_domain(
        domain_name=request.domain_name,
        domain_code=request.domain_code,
        description=request.description,
        business_owner=request.business_owner,
        data_steward=request.data_steward,
        technical_owner=request.technical_owner,
    )
    return {"status": "created", "domain_id": str(domain.domain_id)}


@router.get("/domains")
async def get_all_domains():
    domains = await data_governance_service.repository.find_all_domains()
    return {"domains": [{"domain_id": str(d.domain_id), "name": d.domain_name, "code": d.domain_code} for d in domains]}


@router.get("/domains/{domain_id}")
async def get_domain(domain_id: UUID):
    domain = await data_governance_service.repository.find_domain_by_id(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.post("/ownerships")
async def assign_ownership(request: AssignOwnershipRequest):
    ownership = await data_governance_service.assign_ownership(
        asset_id=request.asset_id,
        asset_name=request.asset_name,
        business_owner=request.business_owner,
        data_steward=request.data_steward,
        technical_owner=request.technical_owner,
        responsibilities=request.responsibilities,
    )
    return {"status": "assigned", "ownership_id": str(ownership.ownership_id)}


@router.get("/ownerships")
async def get_all_ownerships():
    ownerships = await data_governance_service.repository.find_all_ownerships()
    return {"ownerships": [{"id": str(o.ownership_id), "asset": o.asset_name, "owner": o.business_owner} for o in ownerships]}


@router.get("/ownerships/asset/{asset_id}")
async def get_ownership_by_asset(asset_id: UUID):
    ownership = await data_governance_service.repository.find_ownership_by_asset(asset_id)
    if not ownership:
        raise HTTPException(status_code=404, detail="Ownership not found")
    return ownership


@router.post("/policies")
async def create_policy(request: CreatePolicyRequest):
    policy = await data_governance_service.create_policy(
        policy_code=request.policy_code,
        policy_name=request.policy_name,
        policy_type=request.policy_type,
        description=request.description,
        scope=request.scope,
        requirements=request.requirements,
        owner=request.owner,
        approver=request.approver,
    )
    return {"status": "created", "policy_id": str(policy.policy_id)}


@router.get("/policies")
async def get_all_policies():
    policies = await data_governance_service.repository.find_all_policies()
    return {"policies": [{"policy_id": str(p.policy_id), "name": p.policy_name, "type": p.policy_type} for p in policies]}


@router.get("/policies/{policy_id}")
async def get_policy(policy_id: UUID):
    policy = await data_governance_service.repository.find_policy_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/standards")
async def create_standard(request: CreateStandardRequest):
    standard = await data_governance_service.create_standard(
        standard_code=request.standard_code,
        standard_name=request.standard_name,
        standard_type=request.standard_type,
        description=request.description,
        rules=request.rules,
        owner=request.owner,
        domain_applicability=request.domain_applicability,
    )
    return {"status": "created", "standard_id": str(standard.standard_id)}


@router.get("/standards")
async def get_all_standards():
    standards = await data_governance_service.repository.find_all_standards()
    return {"standards": [{"standard_id": str(s.standard_id), "name": s.standard_name, "type": s.standard_type} for s in standards]}


@router.get("/standards/{standard_id}")
async def get_standard(standard_id: UUID):
    standard = await data_governance_service.repository.find_standard_by_id(standard_id)
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard


@router.post("/glossary")
async def add_glossary_term(request: AddGlossaryTermRequest):
    term = await data_governance_service.add_glossary_term(
        term_name=request.term_name,
        term_definition=request.term_definition,
        domain_id=request.domain_id,
        owner=request.owner,
        steward=request.steward,
        synonyms=request.synonyms,
    )
    return {"status": "created", "term_id": str(term.term_id)}


@router.get("/glossary")
async def get_all_glossary_terms():
    terms = await data_governance_service.repository.find_all_glossary_terms()
    return {"terms": [{"term_id": str(t.term_id), "name": t.term_name} for t in terms]}


@router.get("/glossary/search")
async def search_glossary(query: str):
    terms = await data_governance_service.repository.search_glossary(query)
    return {"terms": [{"term_id": str(t.term_id), "name": t.term_name, "definition": t.term_definition} for t in terms]}


@router.get("/glossary/{term_id}")
async def get_glossary_term(term_id: UUID):
    term = await data_governance_service.repository.find_glossary_term_by_id(term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term


@router.post("/access-requests")
async def submit_access_request(request: SubmitAccessRequestRequest):
    access_request = await data_governance_service.submit_access_request(
        requestor=request.requestor,
        requestor_department=request.requestor_department,
        asset_id=request.asset_id,
        asset_name=request.asset_name,
        access_type=request.access_type,
        purpose=request.purpose,
        duration=request.duration,
        justification=request.justification,
    )
    return {"status": "submitted", "request_id": str(access_request.request_id)}


@router.post("/access-requests/{request_id}/approve")
async def approve_access_request(request_id: UUID, approver: str, expiry_date: date):
    access_request = await data_governance_service.approve_access_request(
        request_id=request_id,
        approver=approver,
        expiry_date=expiry_date,
    )
    if not access_request:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "approved", "request_id": str(access_request.request_id)}


@router.get("/access-requests")
async def get_all_access_requests():
    requests = await data_governance_service.repository.find_all_access_requests()
    return {"requests": [{"request_id": str(r.request_id), "requestor": r.requestor, "status": r.status} for r in requests]}


@router.get("/access-requests/pending")
async def get_pending_access_requests():
    requests = await data_governance_service.repository.find_pending_access_requests()
    return {"requests": [{"request_id": str(r.request_id), "requestor": r.requestor, "asset": r.asset_name} for r in requests]}


@router.post("/privacy-assessments")
async def conduct_privacy_assessment(request: ConductPrivacyAssessmentRequest):
    assessment = await data_governance_service.conduct_privacy_assessment(
        asset_id=request.asset_id,
        asset_name=request.asset_name,
        assessor=request.assessor,
        contains_pii=request.contains_pii,
        pii_categories=request.pii_categories,
        data_subjects=request.data_subjects,
        processing_purposes=request.processing_purposes,
        security_controls=request.security_controls,
    )
    return {"status": "completed", "assessment_id": str(assessment.assessment_id), "risk_level": assessment.risk_level}


@router.get("/privacy-assessments")
async def get_all_privacy_assessments():
    assessments = await data_governance_service.repository.find_all_privacy_assessments()
    return {"assessments": [{"id": str(a.assessment_id), "asset": a.asset_name, "risk": a.risk_level} for a in assessments]}


@router.get("/privacy-assessments/high-risk")
async def get_high_risk_assessments():
    assessments = await data_governance_service.repository.find_privacy_assessments_by_risk_level("high")
    return {"assessments": [{"id": str(a.assessment_id), "asset": a.asset_name} for a in assessments]}


@router.post("/metrics")
async def record_metric(request: RecordMetricRequest):
    metric = await data_governance_service.record_metric(
        metric_name=request.metric_name,
        metric_type=request.metric_type,
        current_value=request.current_value,
        target_value=request.target_value,
        threshold_value=request.threshold_value,
        domain_id=request.domain_id,
    )
    return {"status": "recorded", "metric_id": str(metric.metric_id), "metric_status": metric.status}


@router.get("/metrics")
async def get_all_metrics():
    metrics = await data_governance_service.repository.find_all_metrics()
    return {"metrics": [{"metric_id": str(m.metric_id), "name": m.metric_name, "status": m.status} for m in metrics]}


@router.get("/statistics")
async def get_statistics():
    return await data_governance_service.get_statistics()
