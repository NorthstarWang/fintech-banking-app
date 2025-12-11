"""Fraud Case Routes - API endpoints for fraud case management"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.fraud_case_models import (
    FraudCase, CaseStatus, CasePriority, CaseOutcome, CaseNote, CaseEvidence
)
from ..services.fraud_case_service import fraud_case_service


router = APIRouter(prefix="/fraud/cases", tags=["Fraud Cases"])


class CreateCaseRequest(BaseModel):
    customer_id: str
    customer_name: str
    account_id: str
    priority: CasePriority = CasePriority.MEDIUM
    title: str
    description: str
    fraud_type: str
    estimated_loss: float = 0.0


class UpdateCaseRequest(BaseModel):
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    title: Optional[str] = None
    description: Optional[str] = None


class AssignInvestigatorRequest(BaseModel):
    investigator: str


class AddNoteRequest(BaseModel):
    content: str
    created_by: str
    is_internal: bool = True


class AddEvidenceRequest(BaseModel):
    evidence_type: str
    description: str
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    collected_by: str


class CloseCaseRequest(BaseModel):
    outcome: CaseOutcome
    resolution_summary: str
    closed_by: str
    actual_loss: float = 0.0
    prevented_loss: float = 0.0


class LinkAlertRequest(BaseModel):
    alert_id: UUID


@router.post("/", response_model=FraudCase)
async def create_case(request: CreateCaseRequest):
    """Create a new fraud case"""
    case = await fraud_case_service.create_case(
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        account_id=request.account_id,
        priority=request.priority,
        title=request.title,
        description=request.description,
        fraud_type=request.fraud_type,
        estimated_loss=request.estimated_loss
    )
    return case


@router.get("/{case_id}", response_model=FraudCase)
async def get_case(case_id: UUID):
    """Get fraud case by ID"""
    case = await fraud_case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=FraudCase)
async def update_case(case_id: UUID, request: UpdateCaseRequest):
    """Update a fraud case"""
    updates = request.model_dump(exclude_none=True)
    case = await fraud_case_service.update_case(case_id, updates)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/assign", response_model=FraudCase)
async def assign_investigator(case_id: UUID, request: AssignInvestigatorRequest):
    """Assign an investigator to a case"""
    case = await fraud_case_service.assign_investigator(case_id, request.investigator)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/notes", response_model=FraudCase)
async def add_case_note(case_id: UUID, request: AddNoteRequest):
    """Add a note to a case"""
    note = CaseNote(
        content=request.content,
        created_by=request.created_by,
        is_internal=request.is_internal
    )
    case = await fraud_case_service.add_case_note(case_id, note)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/evidence", response_model=FraudCase)
async def add_case_evidence(case_id: UUID, request: AddEvidenceRequest):
    """Add evidence to a case"""
    evidence = CaseEvidence(
        evidence_type=request.evidence_type,
        description=request.description,
        file_name=request.file_name,
        file_url=request.file_url,
        collected_by=request.collected_by
    )
    case = await fraud_case_service.add_case_evidence(case_id, evidence)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/link-alert", response_model=FraudCase)
async def link_alert_to_case(case_id: UUID, request: LinkAlertRequest):
    """Link an alert to a case"""
    case = await fraud_case_service.link_alert(case_id, request.alert_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/close", response_model=FraudCase)
async def close_case(case_id: UUID, request: CloseCaseRequest):
    """Close a fraud case"""
    case = await fraud_case_service.close_case(
        case_id=case_id,
        outcome=request.outcome,
        resolution_summary=request.resolution_summary,
        closed_by=request.closed_by,
        actual_loss=request.actual_loss,
        prevented_loss=request.prevented_loss
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/reopen", response_model=FraudCase)
async def reopen_case(case_id: UUID, reason: str, reopened_by: str):
    """Reopen a closed case"""
    case = await fraud_case_service.reopen_case(case_id, reason, reopened_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/", response_model=List[FraudCase])
async def list_cases(
    status: Optional[CaseStatus] = None,
    priority: Optional[CasePriority] = None,
    investigator: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List fraud cases with optional filters"""
    if status:
        cases = await fraud_case_service.get_cases_by_status(status)
    else:
        cases = await fraud_case_service.get_open_cases()
    return cases[:limit]


@router.get("/open", response_model=List[FraudCase])
async def get_open_cases(limit: int = Query(default=100, le=500)):
    """Get all open fraud cases"""
    return await fraud_case_service.get_open_cases()


@router.get("/customer/{customer_id}", response_model=List[FraudCase])
async def get_customer_cases(customer_id: str, limit: int = Query(default=50, le=200)):
    """Get all cases for a specific customer"""
    return await fraud_case_service.get_cases_by_customer(customer_id)


@router.get("/investigator/{investigator}", response_model=List[FraudCase])
async def get_investigator_cases(investigator: str, limit: int = Query(default=50, le=200)):
    """Get all cases assigned to an investigator"""
    return await fraud_case_service.get_cases_by_investigator(investigator)


@router.get("/statistics/summary")
async def get_case_statistics():
    """Get case statistics"""
    return await fraud_case_service.get_statistics()
