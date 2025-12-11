"""Issue Management API Routes"""

from typing import List, Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.issue_management_models import IssueSource, IssuePriority, IssueStatus
from ..services.issue_management_service import issue_management_service

router = APIRouter(prefix="/issues", tags=["Issue Management"])


class IssueCreateRequest(BaseModel):
    issue_title: str
    source: IssueSource
    priority: IssuePriority
    description: str
    impact: str
    business_unit: str
    identified_by: str
    owner: str
    due_date: date
    source_reference: str = ""


class ActionPlanRequest(BaseModel):
    issue_id: UUID
    action_description: str
    action_type: str
    owner: str
    due_date: date
    evidence_required: List[str]


class IssueUpdateRequest(BaseModel):
    issue_id: UUID
    updated_by: str
    update_type: str
    progress_update: str
    next_steps: str
    blockers: List[str] = []


class ValidationRequest(BaseModel):
    issue_id: UUID
    validator: str
    validation_type: str
    evidence_reviewed: List[str]
    tests_performed: List[str]
    validation_result: str
    findings: str
    recommendation: str


class EscalationRequest(BaseModel):
    issue_id: UUID
    escalated_by: str
    escalation_reason: str
    escalated_to: str
    escalation_level: int
    response_required_by: date


@router.post("/", response_model=dict)
async def create_issue(request: IssueCreateRequest):
    issue = await issue_management_service.create_issue(
        issue_title=request.issue_title, source=request.source, priority=request.priority,
        description=request.description, impact=request.impact, business_unit=request.business_unit,
        identified_by=request.identified_by, owner=request.owner, due_date=request.due_date,
        source_reference=request.source_reference
    )
    return {"issue_id": str(issue.issue_id), "issue_reference": issue.issue_reference}


@router.get("/", response_model=List[dict])
async def list_issues(
    status: Optional[IssueStatus] = None,
    open_only: bool = False,
    owner: Optional[str] = None
):
    if status:
        issues = await issue_management_service.repository.find_issues_by_status(status)
    elif open_only:
        issues = await issue_management_service.repository.find_open_issues()
    elif owner:
        issues = await issue_management_service.repository.find_issues_by_owner(owner)
    else:
        issues = await issue_management_service.repository.find_all_issues()
    return [{"issue_id": str(i.issue_id), "issue_reference": i.issue_reference, "issue_title": i.issue_title, "priority": i.priority.value, "status": i.status.value} for i in issues]


@router.get("/{issue_id}", response_model=dict)
async def get_issue(issue_id: UUID):
    issue = await issue_management_service.repository.find_issue_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {
        "issue_id": str(issue.issue_id),
        "issue_reference": issue.issue_reference,
        "issue_title": issue.issue_title,
        "description": issue.description,
        "priority": issue.priority.value,
        "status": issue.status.value,
        "owner": issue.owner,
        "due_date": str(issue.due_date)
    }


@router.post("/action-plans", response_model=dict)
async def create_action_plan(request: ActionPlanRequest):
    action = await issue_management_service.create_action_plan(
        issue_id=request.issue_id, action_description=request.action_description,
        action_type=request.action_type, owner=request.owner, due_date=request.due_date,
        evidence_required=request.evidence_required
    )
    return {"action_id": str(action.action_id), "action_reference": action.action_reference}


@router.get("/{issue_id}/action-plans", response_model=List[dict])
async def get_issue_action_plans(issue_id: UUID):
    actions = await issue_management_service.repository.find_action_plans_by_issue(issue_id)
    return [{"action_id": str(a.action_id), "action_reference": a.action_reference, "status": a.status, "progress_percentage": a.progress_percentage} for a in actions]


@router.post("/action-plans/{action_id}/progress", response_model=dict)
async def update_action_progress(
    action_id: UUID,
    progress_percentage: int = Query(...),
    evidence_provided: List[str] = Query(default=[]),
    comments: str = Query(default="")
):
    action = await issue_management_service.update_action_progress(
        action_id, progress_percentage, evidence_provided, comments
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action plan not found")
    return {"action_id": str(action.action_id), "status": action.status, "progress_percentage": action.progress_percentage}


@router.post("/updates", response_model=dict)
async def post_update(request: IssueUpdateRequest):
    update = await issue_management_service.update_issue(
        issue_id=request.issue_id, updated_by=request.updated_by, update_type=request.update_type,
        progress_update=request.progress_update, next_steps=request.next_steps, blockers=request.blockers
    )
    return {"update_id": str(update.update_id)}


@router.post("/{issue_id}/status", response_model=dict)
async def change_status(issue_id: UUID, new_status: IssueStatus = Query(...), updated_by: str = Query(...)):
    issue = await issue_management_service.change_issue_status(issue_id, new_status, updated_by)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"issue_id": str(issue.issue_id), "status": issue.status.value}


@router.post("/validations", response_model=dict)
async def validate_issue(request: ValidationRequest):
    validation = await issue_management_service.validate_issue(
        issue_id=request.issue_id, validator=request.validator, validation_type=request.validation_type,
        evidence_reviewed=request.evidence_reviewed, tests_performed=request.tests_performed,
        validation_result=request.validation_result, findings=request.findings,
        recommendation=request.recommendation
    )
    return {"validation_id": str(validation.validation_id), "validation_result": validation.validation_result}


@router.post("/escalations", response_model=dict)
async def escalate_issue(request: EscalationRequest):
    escalation = await issue_management_service.escalate_issue(
        issue_id=request.issue_id, escalated_by=request.escalated_by,
        escalation_reason=request.escalation_reason, escalated_to=request.escalated_to,
        escalation_level=request.escalation_level, response_required_by=request.response_required_by
    )
    return {"escalation_id": str(escalation.escalation_id)}


@router.post("/{issue_id}/extend", response_model=dict)
async def extend_due_date(issue_id: UUID, new_due_date: date = Query(...), updated_by: str = Query(...), reason: str = Query(...)):
    issue = await issue_management_service.extend_due_date(issue_id, new_due_date, updated_by, reason)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"issue_id": str(issue.issue_id), "extended_due_date": str(issue.extended_due_date)}


@router.get("/statistics", response_model=dict)
async def get_issue_statistics():
    return await issue_management_service.get_statistics()
