"""Policy Management API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.policy_models import PolicyCategory
from ..services.policy_service import policy_service

router = APIRouter(prefix="/policies", tags=["Policy Management"])


class PolicyCreateRequest(BaseModel):
    policy_code: str
    policy_name: str
    policy_category: PolicyCategory
    description: str
    purpose: str
    scope: str
    policy_statement: str
    owner: str
    approver: str
    created_by: str


class ExceptionRequest(BaseModel):
    policy_id: UUID
    requestor: str
    business_unit: str
    exception_type: str
    description: str
    justification: str
    risk_assessment: str
    compensating_controls: List[str]
    duration: str
    expiry_date: date


class AttestationRequest(BaseModel):
    policy_id: UUID
    attestation_period: str
    employee_id: str
    employee_name: str
    department: str
    acknowledged: bool
    understood: bool
    compliant: bool


class ReviewRequest(BaseModel):
    policy_id: UUID
    reviewer: str
    review_type: str
    current_relevance: str
    regulatory_alignment: str
    operational_effectiveness: str
    gaps_identified: List[str]
    recommendations: List[str]
    changes_required: bool


@router.post("/", response_model=dict)
async def create_policy(request: PolicyCreateRequest):
    policy = await policy_service.create_policy(
        policy_code=request.policy_code, policy_name=request.policy_name,
        policy_category=request.policy_category, description=request.description,
        purpose=request.purpose, scope=request.scope, policy_statement=request.policy_statement,
        owner=request.owner, approver=request.approver, created_by=request.created_by
    )
    return {"policy_id": str(policy.policy_id), "policy_code": policy.policy_code}


@router.get("/", response_model=List[dict])
async def list_policies(active_only: bool = False, category: Optional[str] = None):
    if category:
        policies = await policy_service.repository.find_policies_by_category(category)
    elif active_only:
        policies = await policy_service.repository.find_active_policies()
    else:
        policies = await policy_service.repository.find_all_policies()
    return [{"policy_id": str(p.policy_id), "policy_code": p.policy_code, "policy_name": p.policy_name, "status": p.status.value} for p in policies]


@router.post("/{policy_id}/approve", response_model=dict)
async def approve_policy(policy_id: UUID):
    policy = await policy_service.approve_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy_id": str(policy.policy_id), "status": policy.status.value}


@router.post("/{policy_id}/activate", response_model=dict)
async def activate_policy(policy_id: UUID):
    policy = await policy_service.activate_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found or not approved")
    return {"policy_id": str(policy.policy_id), "status": policy.status.value}


@router.post("/exceptions", response_model=dict)
async def request_exception(request: ExceptionRequest):
    exception = await policy_service.request_exception(
        policy_id=request.policy_id, requestor=request.requestor,
        business_unit=request.business_unit, exception_type=request.exception_type,
        description=request.description, justification=request.justification,
        risk_assessment=request.risk_assessment, compensating_controls=request.compensating_controls,
        duration=request.duration, expiry_date=request.expiry_date
    )
    return {"exception_id": str(exception.exception_id), "exception_reference": exception.exception_reference}


@router.get("/exceptions", response_model=List[dict])
async def list_exceptions(active_only: bool = False):
    if active_only:
        exceptions = await policy_service.repository.find_active_exceptions()
    else:
        exceptions = await policy_service.repository.find_all_exceptions()
    return [{"exception_id": str(e.exception_id), "exception_reference": e.exception_reference, "status": e.status} for e in exceptions]


@router.post("/exceptions/{exception_id}/approve", response_model=dict)
async def approve_exception(exception_id: UUID, approved_by: str = Query(...)):
    exception = await policy_service.approve_exception(exception_id, approved_by)
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    return {"exception_id": str(exception.exception_id), "status": exception.status}


@router.post("/attestations", response_model=dict)
async def record_attestation(request: AttestationRequest):
    attestation = await policy_service.record_attestation(
        policy_id=request.policy_id, attestation_period=request.attestation_period,
        employee_id=request.employee_id, employee_name=request.employee_name,
        department=request.department, acknowledged=request.acknowledged,
        understood=request.understood, compliant=request.compliant
    )
    return {"attestation_id": str(attestation.attestation_id)}


@router.get("/{policy_id}/attestations", response_model=List[dict])
async def get_policy_attestations(policy_id: UUID):
    attestations = await policy_service.repository.find_attestations_by_policy(policy_id)
    return [{"attestation_id": str(a.attestation_id), "employee_name": a.employee_name, "compliant": a.compliant} for a in attestations]


@router.post("/reviews", response_model=dict)
async def review_policy(request: ReviewRequest):
    review = await policy_service.review_policy(
        policy_id=request.policy_id, reviewer=request.reviewer, review_type=request.review_type,
        current_relevance=request.current_relevance, regulatory_alignment=request.regulatory_alignment,
        operational_effectiveness=request.operational_effectiveness,
        gaps_identified=request.gaps_identified, recommendations=request.recommendations,
        changes_required=request.changes_required
    )
    return {"review_id": str(review.review_id), "changes_required": review.changes_required}


@router.get("/statistics", response_model=dict)
async def get_policy_statistics():
    return await policy_service.get_statistics()
