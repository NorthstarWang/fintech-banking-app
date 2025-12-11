"""
SAR Routes

API endpoints for SAR management.
"""

from typing import List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.sar_models import (
    SAR, SARSummary, SARStatistics, SARStatus, SARType,
    SARCreateRequest, SARUpdateRequest, SARSearchCriteria,
    SubjectInfo, SuspiciousActivity, TransactionDetail, SARDocument
)
from ..services.sar_service import sar_service

router = APIRouter(prefix="/aml/sars", tags=["SAR Management"])


@router.post("/", response_model=SAR)
async def create_sar(request: SARCreateRequest, created_by: str = "system"):
    """Create a new SAR"""
    return await sar_service.create_sar(request, created_by)


@router.get("/{sar_id}", response_model=SAR)
async def get_sar(sar_id: UUID):
    """Get SAR by ID"""
    sar = await sar_service.get_sar(sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return sar


@router.put("/{sar_id}", response_model=SAR)
async def update_sar(sar_id: UUID, request: SARUpdateRequest, updated_by: str = "system"):
    """Update a SAR"""
    sar = await sar_service.update_sar(sar_id, request, updated_by)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return sar


@router.post("/{sar_id}/subjects")
async def add_subject(sar_id: UUID, subject: SubjectInfo):
    """Add subject to SAR"""
    sar = await sar_service.add_subject(sar_id, subject)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return {"status": "success"}


@router.post("/{sar_id}/activities")
async def add_activity(sar_id: UUID, activity: SuspiciousActivity):
    """Add suspicious activity to SAR"""
    sar = await sar_service.add_activity(sar_id, activity)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return {"status": "success"}


@router.post("/{sar_id}/transactions")
async def add_transaction(sar_id: UUID, transaction: TransactionDetail):
    """Add transaction detail to SAR"""
    sar = await sar_service.add_transaction(sar_id, transaction)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return {"status": "success"}


@router.post("/{sar_id}/narrative")
async def add_narrative(sar_id: UUID, section: str, content: str, author: str = "system"):
    """Add or update narrative section"""
    narrative = await sar_service.add_narrative(sar_id, section, content, author)
    if not narrative:
        raise HTTPException(status_code=404, detail="SAR not found")
    return narrative


@router.post("/{sar_id}/documents")
async def add_document(sar_id: UUID, document: SARDocument):
    """Add supporting document to SAR"""
    sar = await sar_service.add_document(sar_id, document)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return {"status": "success"}


@router.post("/{sar_id}/submit-for-approval")
async def submit_for_approval(sar_id: UUID, submitted_by: str = "system"):
    """Submit SAR for approval"""
    sar = await sar_service.submit_for_approval(sar_id, submitted_by)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return sar


@router.post("/{sar_id}/approve")
async def approve_sar(
    sar_id: UUID, approver_id: str, approver_name: str, approver_role: str, comments: str = None
):
    """Approve SAR"""
    sar = await sar_service.approve_sar(sar_id, approver_id, approver_name, approver_role, comments)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return sar


@router.post("/{sar_id}/reject")
async def reject_sar(sar_id: UUID, approver_id: str, approver_name: str, approver_role: str, reason: str):
    """Reject SAR for revisions"""
    sar = await sar_service.reject_sar(sar_id, approver_id, approver_name, approver_role, reason)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return sar


@router.post("/{sar_id}/file")
async def file_sar(sar_id: UUID, submission_method: str = "efiling"):
    """File SAR with FinCEN"""
    try:
        sar = await sar_service.file_sar(sar_id, submission_method)
        if not sar:
            raise HTTPException(status_code=404, detail="SAR not found")
        return sar
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sar_id}/acknowledge")
async def acknowledge_sar(sar_id: UUID, acknowledgment_number: str):
    """Record SAR acknowledgment from FinCEN"""
    sar = await sar_service.acknowledge_sar(sar_id, acknowledgment_number)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")
    return sar


@router.post("/search", response_model=List[SARSummary])
async def search_sars(criteria: SARSearchCriteria):
    """Search SARs based on criteria"""
    return await sar_service.search_sars(criteria)


@router.get("/statistics", response_model=SARStatistics)
async def get_statistics():
    """Get SAR statistics"""
    return await sar_service.get_statistics()
