"""External Audit API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.external_audit_models import ExternalAuditType, AuditOpinion
from ..services.external_audit_service import external_audit_service

router = APIRouter(prefix="/external-audit", tags=["External Audit"])


class EngagementCreateRequest(BaseModel):
    audit_firm: str
    audit_type: ExternalAuditType
    fiscal_year: int
    engagement_partner: str
    engagement_manager: str
    engagement_letter_date: date
    scope: str
    materiality_threshold: Decimal
    planned_start_date: date
    planned_end_date: date
    fee_estimate: Decimal
    internal_coordinator: str


class PBCCreateRequest(BaseModel):
    engagement_id: UUID
    item_description: str
    category: str
    requested_by: str
    due_date: date
    assigned_to: str
    priority: str = "normal"


class AdjustmentRequest(BaseModel):
    engagement_id: UUID
    adjustment_type: str
    account_affected: str
    debit_amount: Decimal
    credit_amount: Decimal
    description: str
    proposed_by: str


class FindingRequest(BaseModel):
    engagement_id: UUID
    finding_type: str
    description: str
    severity: str
    management_letter_item: bool = False
    significant_deficiency: bool = False
    material_weakness: bool = False


class OpinionRequest(BaseModel):
    engagement_id: UUID
    opinion_type: AuditOpinion
    basis_for_opinion: str
    signed_by: str
    firm_name: str
    going_concern_doubt: bool = False


@router.post("/engagements", response_model=dict)
async def create_engagement(request: EngagementCreateRequest):
    engagement = await external_audit_service.create_engagement(
        audit_firm=request.audit_firm, audit_type=request.audit_type,
        fiscal_year=request.fiscal_year, engagement_partner=request.engagement_partner,
        engagement_manager=request.engagement_manager, engagement_letter_date=request.engagement_letter_date,
        scope=request.scope, materiality_threshold=request.materiality_threshold,
        planned_start_date=request.planned_start_date, planned_end_date=request.planned_end_date,
        fee_estimate=request.fee_estimate, internal_coordinator=request.internal_coordinator
    )
    return {"engagement_id": str(engagement.engagement_id), "engagement_reference": engagement.engagement_reference}


@router.get("/engagements", response_model=List[dict])
async def list_engagements(fiscal_year: Optional[int] = None):
    if fiscal_year:
        engagements = await external_audit_service.repository.find_engagements_by_year(fiscal_year)
    else:
        engagements = await external_audit_service.repository.find_all_engagements()
    return [{"engagement_id": str(e.engagement_id), "engagement_reference": e.engagement_reference, "audit_firm": e.audit_firm, "status": e.status} for e in engagements]


@router.post("/engagements/{engagement_id}/start", response_model=dict)
async def start_engagement(engagement_id: UUID):
    engagement = await external_audit_service.start_engagement(engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return {"engagement_id": str(engagement.engagement_id), "status": engagement.status}


@router.post("/pbc-requests", response_model=dict)
async def create_pbc_request(request: PBCCreateRequest):
    pbc = await external_audit_service.create_pbc_request(
        engagement_id=request.engagement_id, item_description=request.item_description,
        category=request.category, requested_by=request.requested_by,
        due_date=request.due_date, assigned_to=request.assigned_to, priority=request.priority
    )
    return {"pbc_id": str(pbc.pbc_id), "pbc_reference": pbc.pbc_reference}


@router.get("/pbc-requests", response_model=List[dict])
async def list_pbc_requests(engagement_id: Optional[UUID] = None, pending_only: bool = False):
    if engagement_id:
        pbcs = await external_audit_service.repository.find_pbcs_by_engagement(engagement_id)
    elif pending_only:
        pbcs = await external_audit_service.repository.find_pending_pbcs()
    else:
        pbcs = await external_audit_service.repository.find_all_pbcs()
    return [{"pbc_id": str(p.pbc_id), "pbc_reference": p.pbc_reference, "item_description": p.item_description, "status": p.status} for p in pbcs]


@router.post("/pbc-requests/{pbc_id}/submit", response_model=dict)
async def submit_pbc(pbc_id: UUID, submitted_by: str = Query(...), file_references: List[str] = Query(default=[])):
    pbc = await external_audit_service.submit_pbc(pbc_id, submitted_by, file_references)
    if not pbc:
        raise HTTPException(status_code=404, detail="PBC request not found")
    return {"pbc_id": str(pbc.pbc_id), "status": pbc.status}


@router.post("/adjustments", response_model=dict)
async def record_adjustment(request: AdjustmentRequest):
    adjustment = await external_audit_service.record_adjustment(
        engagement_id=request.engagement_id, adjustment_type=request.adjustment_type,
        account_affected=request.account_affected, debit_amount=request.debit_amount,
        credit_amount=request.credit_amount, description=request.description,
        proposed_by=request.proposed_by
    )
    return {"adjustment_id": str(adjustment.adjustment_id), "adjustment_reference": adjustment.adjustment_reference}


@router.post("/adjustments/{adjustment_id}/accept", response_model=dict)
async def accept_adjustment(adjustment_id: UUID):
    adjustment = await external_audit_service.accept_adjustment(adjustment_id)
    if not adjustment:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    return {"adjustment_id": str(adjustment.adjustment_id), "management_accepted": adjustment.management_accepted}


@router.post("/findings", response_model=dict)
async def record_finding(request: FindingRequest):
    finding = await external_audit_service.record_finding(
        engagement_id=request.engagement_id, finding_type=request.finding_type,
        description=request.description, severity=request.severity,
        management_letter_item=request.management_letter_item,
        significant_deficiency=request.significant_deficiency,
        material_weakness=request.material_weakness
    )
    return {"finding_id": str(finding.finding_id), "finding_reference": finding.finding_reference}


@router.post("/opinions", response_model=dict)
async def issue_opinion(request: OpinionRequest):
    opinion = await external_audit_service.issue_opinion(
        engagement_id=request.engagement_id, opinion_type=request.opinion_type,
        basis_for_opinion=request.basis_for_opinion, signed_by=request.signed_by,
        firm_name=request.firm_name, going_concern_doubt=request.going_concern_doubt
    )
    return {"opinion_id": str(opinion.opinion_id), "opinion_type": opinion.opinion_type.value}


@router.get("/statistics", response_model=dict)
async def get_external_audit_statistics():
    return await external_audit_service.get_statistics()
