"""
AML Case Routes

API endpoints for AML case management.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.case_models import (
    AMLCase, CaseSummary, CaseStatistics, CaseStatus,
    CaseCreateRequest, CaseUpdateRequest, CaseSearchCriteria,
    InvestigationFinding, CaseDocument, RelatedEntity
)
from ..services.case_service import case_service

router = APIRouter(prefix="/aml/cases", tags=["AML Cases"])


@router.post("/", response_model=AMLCase)
async def create_case(request: CaseCreateRequest, created_by: str = "system"):
    """Create a new AML case"""
    return await case_service.create_case(request, created_by)


@router.get("/{case_id}", response_model=AMLCase)
async def get_case(case_id: UUID):
    """Get case by ID"""
    case = await case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=AMLCase)
async def update_case(case_id: UUID, request: CaseUpdateRequest, updated_by: str = "system"):
    """Update a case"""
    case = await case_service.update_case(case_id, request, updated_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/open")
async def open_case(case_id: UUID, opened_by: str = "system"):
    """Open a case for investigation"""
    case = await case_service.open_case(case_id, opened_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/assign")
async def assign_case(case_id: UUID, assignee: str, role: str = "investigator", assigned_by: str = "system"):
    """Assign case to an investigator"""
    case = await case_service.assign_case(case_id, assignee, assigned_by, role)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/findings")
async def add_finding(case_id: UUID, finding: InvestigationFinding):
    """Add investigation finding to case"""
    case = await case_service.add_finding(case_id, finding)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "success"}


@router.post("/{case_id}/documents")
async def add_document(case_id: UUID, document: CaseDocument):
    """Add document to case"""
    case = await case_service.add_document(case_id, document)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "success"}


@router.post("/{case_id}/entities")
async def add_related_entity(case_id: UUID, entity: RelatedEntity, added_by: str = "system"):
    """Add related entity to case"""
    case = await case_service.add_related_entity(case_id, entity, added_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "success"}


@router.post("/{case_id}/escalate")
async def escalate_case(case_id: UUID, reason: str, escalated_by: str = "system"):
    """Escalate a case"""
    case = await case_service.escalate_case(case_id, escalated_by, reason)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/close")
async def close_case(
    case_id: UUID, resolution_type: str, resolution_summary: str, closed_by: str = "system"
):
    """Close a case"""
    case = await case_service.close_case(case_id, closed_by, resolution_type, resolution_summary)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/search", response_model=List[CaseSummary])
async def search_cases(criteria: CaseSearchCriteria):
    """Search cases based on criteria"""
    return await case_service.search_cases(criteria)


@router.get("/statistics", response_model=CaseStatistics)
async def get_statistics():
    """Get case statistics"""
    return await case_service.get_statistics()
