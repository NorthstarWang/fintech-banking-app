"""Internal Audit API Routes"""

from typing import List, Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.internal_audit_models import AuditType, AuditStatus, FindingSeverity
from ..services.internal_audit_service import internal_audit_service

router = APIRouter(prefix="/internal-audit", tags=["Internal Audit"])


class AuditCreateRequest(BaseModel):
    audit_name: str
    audit_type: AuditType
    audit_scope: str
    audit_objectives: List[str]
    business_unit: str
    audit_period_start: date
    audit_period_end: date
    planned_start_date: date
    planned_end_date: date
    lead_auditor: str
    audit_team: List[str]
    budgeted_hours: int


class WorkpaperCreateRequest(BaseModel):
    audit_id: UUID
    workpaper_title: str
    workpaper_type: str
    section: str
    prepared_by: str
    testing_objective: str
    testing_procedure: str
    sample_size: int
    population_size: int


class FindingCreateRequest(BaseModel):
    audit_id: UUID
    finding_title: str
    severity: FindingSeverity
    condition: str
    criteria: str
    cause: str
    effect: str
    recommendation: str


class FindingResponseRequest(BaseModel):
    management_response: str
    action_plan: str
    action_owner: str
    target_date: date


@router.post("/audits", response_model=dict)
async def create_audit(request: AuditCreateRequest):
    audit = await internal_audit_service.create_audit(
        audit_name=request.audit_name, audit_type=request.audit_type,
        audit_scope=request.audit_scope, audit_objectives=request.audit_objectives,
        business_unit=request.business_unit, audit_period_start=request.audit_period_start,
        audit_period_end=request.audit_period_end, planned_start_date=request.planned_start_date,
        planned_end_date=request.planned_end_date, lead_auditor=request.lead_auditor,
        audit_team=request.audit_team, budgeted_hours=request.budgeted_hours
    )
    return {"audit_id": str(audit.audit_id), "audit_reference": audit.audit_reference}


@router.get("/audits", response_model=List[dict])
async def list_audits(status: Optional[AuditStatus] = None, business_unit: Optional[str] = None):
    if status:
        audits = await internal_audit_service.repository.find_audits_by_status(status)
    elif business_unit:
        audits = await internal_audit_service.repository.find_audits_by_business_unit(business_unit)
    else:
        audits = await internal_audit_service.repository.find_all_audits()
    return [{"audit_id": str(a.audit_id), "audit_reference": a.audit_reference, "audit_name": a.audit_name, "status": a.status.value} for a in audits]


@router.post("/audits/{audit_id}/start", response_model=dict)
async def start_audit(audit_id: UUID):
    audit = await internal_audit_service.start_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {"audit_id": str(audit.audit_id), "status": audit.status.value}


@router.post("/audits/{audit_id}/complete", response_model=dict)
async def complete_audit(audit_id: UUID):
    audit = await internal_audit_service.complete_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {"audit_id": str(audit.audit_id), "status": audit.status.value}


@router.post("/workpapers", response_model=dict)
async def create_workpaper(request: WorkpaperCreateRequest):
    workpaper = await internal_audit_service.create_workpaper(
        audit_id=request.audit_id, workpaper_title=request.workpaper_title,
        workpaper_type=request.workpaper_type, section=request.section,
        prepared_by=request.prepared_by, testing_objective=request.testing_objective,
        testing_procedure=request.testing_procedure, sample_size=request.sample_size,
        population_size=request.population_size
    )
    return {"workpaper_id": str(workpaper.workpaper_id), "workpaper_reference": workpaper.workpaper_reference}


@router.get("/workpapers/{audit_id}", response_model=List[dict])
async def get_audit_workpapers(audit_id: UUID):
    workpapers = await internal_audit_service.repository.find_workpapers_by_audit(audit_id)
    return [{"workpaper_id": str(w.workpaper_id), "workpaper_title": w.workpaper_title, "status": w.status} for w in workpapers]


@router.post("/findings", response_model=dict)
async def create_finding(request: FindingCreateRequest):
    finding = await internal_audit_service.create_finding(
        audit_id=request.audit_id, finding_title=request.finding_title, severity=request.severity,
        condition=request.condition, criteria=request.criteria, cause=request.cause,
        effect=request.effect, recommendation=request.recommendation
    )
    return {"finding_id": str(finding.finding_id), "finding_reference": finding.finding_reference}


@router.get("/findings", response_model=List[dict])
async def list_findings(audit_id: Optional[UUID] = None, open_only: bool = False):
    if audit_id:
        findings = await internal_audit_service.repository.find_findings_by_audit(audit_id)
    elif open_only:
        findings = await internal_audit_service.repository.find_open_findings()
    else:
        findings = await internal_audit_service.repository.find_all_findings()
    return [{"finding_id": str(f.finding_id), "finding_reference": f.finding_reference, "severity": f.severity.value, "status": f.status} for f in findings]


@router.post("/findings/{finding_id}/respond", response_model=dict)
async def respond_to_finding(finding_id: UUID, request: FindingResponseRequest):
    finding = await internal_audit_service.respond_to_finding(
        finding_id=finding_id, management_response=request.management_response,
        action_plan=request.action_plan, action_owner=request.action_owner,
        target_date=request.target_date
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"finding_id": str(finding.finding_id), "status": finding.status}


@router.get("/statistics", response_model=dict)
async def get_internal_audit_statistics():
    return await internal_audit_service.get_statistics()
