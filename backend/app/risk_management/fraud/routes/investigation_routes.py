"""Investigation Routes - API endpoints for fraud investigation management"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.fraud_investigation_models import (
    FraudInvestigation, DisputeRecord, InvestigationTemplate,
    InvestigationStatus, InvestigationType, InvestigationOutcome,
    CustomerContact
)
from ..services.investigation_service import investigation_service


router = APIRouter(prefix="/fraud/investigations", tags=["Fraud Investigations"])


class CreateInvestigationRequest(BaseModel):
    case_id: UUID
    customer_id: str
    customer_name: str
    disputed_amount: float
    investigation_type: InvestigationType = InvestigationType.STANDARD


class UpdateStatusRequest(BaseModel):
    status: InvestigationStatus


class AssignInvestigatorRequest(BaseModel):
    investigator: str


class CompleteStepRequest(BaseModel):
    step_index: int
    result: str
    notes: str
    completed_by: str


class CustomerContactRequest(BaseModel):
    contact_method: str
    contact_result: str
    notes: str
    contacted_by: str


class SetOutcomeRequest(BaseModel):
    outcome: InvestigationOutcome
    reason: str


class ProcessRefundRequest(BaseModel):
    refund_amount: float


class CreateDisputeRequest(BaseModel):
    investigation_id: UUID
    customer_id: str
    account_id: str
    transaction_id: str
    amount: float
    reason: str
    statement: str


@router.post("/", response_model=FraudInvestigation)
async def create_investigation(request: CreateInvestigationRequest):
    """Create a new fraud investigation"""
    investigation = await investigation_service.create_investigation(
        case_id=request.case_id,
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        disputed_amount=request.disputed_amount,
        investigation_type=request.investigation_type
    )
    return investigation


@router.get("/{investigation_id}", response_model=FraudInvestigation)
async def get_investigation(investigation_id: UUID):
    """Get investigation by ID"""
    investigation = await investigation_service.get_investigation(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.put("/{investigation_id}/status", response_model=FraudInvestigation)
async def update_status(investigation_id: UUID, request: UpdateStatusRequest):
    """Update investigation status"""
    investigation = await investigation_service.update_status(
        investigation_id, request.status
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.post("/{investigation_id}/assign", response_model=FraudInvestigation)
async def assign_investigator(investigation_id: UUID, request: AssignInvestigatorRequest):
    """Assign an investigator"""
    investigation = await investigation_service.assign_investigator(
        investigation_id, request.investigator
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.post("/{investigation_id}/steps/complete", response_model=FraudInvestigation)
async def complete_step(investigation_id: UUID, request: CompleteStepRequest):
    """Complete an investigation step"""
    investigation = await investigation_service.complete_step(
        investigation_id=investigation_id,
        step_index=request.step_index,
        result=request.result,
        notes=request.notes,
        completed_by=request.completed_by
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found or invalid step")
    return investigation


@router.post("/{investigation_id}/contact", response_model=FraudInvestigation)
async def record_customer_contact(investigation_id: UUID, request: CustomerContactRequest):
    """Record customer contact"""
    contact = CustomerContact(
        contact_method=request.contact_method,
        contact_result=request.contact_result,
        notes=request.notes,
        contacted_by=request.contacted_by
    )
    investigation = await investigation_service.record_customer_contact(
        investigation_id, contact
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.post("/{investigation_id}/outcome", response_model=FraudInvestigation)
async def set_outcome(investigation_id: UUID, request: SetOutcomeRequest):
    """Set investigation outcome"""
    investigation = await investigation_service.set_outcome(
        investigation_id, request.outcome, request.reason
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.post("/{investigation_id}/refund", response_model=FraudInvestigation)
async def process_refund(investigation_id: UUID, request: ProcessRefundRequest):
    """Process a refund for the investigation"""
    investigation = await investigation_service.process_refund(
        investigation_id, request.refund_amount
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.get("/", response_model=List[FraudInvestigation])
async def list_investigations(
    status: Optional[InvestigationStatus] = None,
    investigation_type: Optional[InvestigationType] = None,
    customer_id: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List investigations with optional filters"""
    # This would be enhanced with actual filtering
    return []


@router.get("/open")
async def get_open_investigations(limit: int = Query(default=100, le=500)):
    """Get all open investigations"""
    return {"open_investigations": []}


@router.get("/overdue")
async def get_overdue_investigations(limit: int = Query(default=100, le=500)):
    """Get all overdue investigations"""
    return {"overdue_investigations": []}


@router.get("/customer/{customer_id}")
async def get_customer_investigations(
    customer_id: str,
    limit: int = Query(default=50, le=200)
):
    """Get investigations for a customer"""
    return {"customer_id": customer_id, "investigations": []}


@router.post("/disputes", response_model=DisputeRecord)
async def create_dispute(request: CreateDisputeRequest):
    """Create a dispute record"""
    dispute = await investigation_service.create_dispute(
        investigation_id=request.investigation_id,
        customer_id=request.customer_id,
        account_id=request.account_id,
        transaction_id=request.transaction_id,
        amount=request.amount,
        reason=request.reason,
        statement=request.statement
    )
    return dispute


@router.get("/disputes/{dispute_id}", response_model=DisputeRecord)
async def get_dispute(dispute_id: UUID):
    """Get dispute by ID"""
    # Would query the repository
    raise HTTPException(status_code=404, detail="Dispute not found")


@router.get("/disputes")
async def list_disputes(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """List disputes"""
    return {"disputes": []}


@router.get("/statistics/summary")
async def get_investigation_statistics():
    """Get investigation statistics"""
    return await investigation_service.get_statistics()
