"""Sanctions Compliance API Routes"""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.sanctions_models import (
    SanctionsList, ScreeningType, AlertStatus
)
from ..services.sanctions_service import sanctions_service

router = APIRouter(prefix="/sanctions", tags=["Sanctions Compliance"])


class ScreeningRequest(BaseModel):
    screening_type: ScreeningType
    subject_type: str
    subject_name: str
    requestor: str
    lists_to_screen: List[SanctionsList]
    country: Optional[str] = None
    date_of_birth: Optional[str] = None


class AlertReviewRequest(BaseModel):
    decision: str
    decision_rationale: str
    decided_by: str


class CaseCreateRequest(BaseModel):
    case_type: str
    source_alert_ids: List[UUID]
    assigned_to: str
    priority: str
    customer_id: Optional[str] = None
    transaction_ids: Optional[List[str]] = None


class BlockTransactionRequest(BaseModel):
    transaction_id: str
    transaction_type: str
    amount: Decimal
    currency: str
    originator: str
    originator_account: str
    beneficiary: str
    beneficiary_account: str
    blocking_reason: str
    list_source: SanctionsList
    matched_entry: str


class ListUpdateRequest(BaseModel):
    list_source: SanctionsList
    update_type: str
    entries_added: int
    entries_removed: int
    entries_modified: int
    file_reference: str
    processed_by: str


@router.post("/screen", response_model=dict)
async def screen_entity(request: ScreeningRequest):
    """Screen an entity against sanctions lists"""
    result = await sanctions_service.screen_entity(
        screening_type=request.screening_type, subject_type=request.subject_type,
        subject_name=request.subject_name, requestor=request.requestor,
        lists_to_screen=request.lists_to_screen, country=request.country,
        date_of_birth=request.date_of_birth
    )
    return {
        "request_id": str(result.request_id),
        "request_reference": result.request_reference,
        "matches_found": result.matches_found,
        "status": result.status
    }


@router.get("/screenings", response_model=List[dict])
async def list_screenings(
    screening_type: Optional[str] = None,
    with_matches_only: bool = False
):
    """List screening requests"""
    if screening_type:
        requests = await sanctions_service.repository.find_requests_by_type(screening_type)
    elif with_matches_only:
        requests = await sanctions_service.repository.find_requests_with_matches()
    else:
        requests = await sanctions_service.repository.find_all_requests()
    return [{"request_id": str(r.request_id), "request_reference": r.request_reference, "subject_name": r.subject_name, "matches_found": r.matches_found} for r in requests]


@router.get("/screenings/{request_id}", response_model=dict)
async def get_screening(request_id: UUID):
    """Get a specific screening request"""
    request = await sanctions_service.repository.find_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Screening request not found")
    return {
        "request_id": str(request.request_id),
        "request_reference": request.request_reference,
        "subject_name": request.subject_name,
        "screening_type": request.screening_type.value,
        "matches_found": request.matches_found,
        "status": request.status
    }


@router.get("/alerts", response_model=List[dict])
async def list_alerts(status: Optional[AlertStatus] = None, pending_only: bool = False):
    """List screening alerts"""
    if status:
        alerts = await sanctions_service.repository.find_alerts_by_status(status)
    elif pending_only:
        alerts = await sanctions_service.repository.find_pending_alerts()
    else:
        alerts = await sanctions_service.repository.find_all_alerts()
    return [{"alert_id": str(a.alert_id), "alert_reference": a.alert_reference, "matched_name": a.matched_name, "match_score": float(a.match_score)} for a in alerts]


@router.get("/alerts/{alert_id}", response_model=dict)
async def get_alert(alert_id: UUID):
    """Get a specific alert"""
    alert = await sanctions_service.repository.find_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "alert_id": str(alert.alert_id),
        "alert_reference": alert.alert_reference,
        "subject_name": alert.subject_name,
        "matched_name": alert.matched_name,
        "match_strength": alert.match_strength.value,
        "match_score": float(alert.match_score),
        "status": alert.status.value
    }


@router.post("/alerts/{alert_id}/review", response_model=dict)
async def review_alert(alert_id: UUID, request: AlertReviewRequest):
    """Review and decide on an alert"""
    alert = await sanctions_service.review_alert(
        alert_id=alert_id, decision=request.decision,
        decision_rationale=request.decision_rationale, decided_by=request.decided_by
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert_id": str(alert.alert_id), "status": alert.status.value, "decision": alert.decision}


@router.post("/cases", response_model=dict)
async def create_case(request: CaseCreateRequest):
    """Create a sanctions case"""
    case = await sanctions_service.create_case(
        case_type=request.case_type, source_alert_ids=request.source_alert_ids,
        assigned_to=request.assigned_to, priority=request.priority,
        customer_id=request.customer_id, transaction_ids=request.transaction_ids
    )
    return {"case_id": str(case.case_id), "case_reference": case.case_reference}


@router.get("/cases", response_model=List[dict])
async def list_cases(open_only: bool = False, assigned_to: Optional[str] = None):
    """List sanctions cases"""
    if open_only:
        cases = await sanctions_service.repository.find_open_cases()
    elif assigned_to:
        cases = await sanctions_service.repository.find_cases_by_assignee(assigned_to)
    else:
        cases = await sanctions_service.repository.find_all_cases()
    return [{"case_id": str(c.case_id), "case_reference": c.case_reference, "case_type": c.case_type, "priority": c.priority} for c in cases]


@router.get("/cases/{case_id}", response_model=dict)
async def get_case(case_id: UUID):
    """Get a specific case"""
    case = await sanctions_service.repository.find_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {
        "case_id": str(case.case_id),
        "case_reference": case.case_reference,
        "case_type": case.case_type,
        "case_status": case.case_status,
        "assigned_to": case.assigned_to,
        "priority": case.priority
    }


@router.post("/cases/{case_id}/close", response_model=dict)
async def close_case(case_id: UUID, final_decision: str = Query(...), closed_by: str = Query(...)):
    """Close a sanctions case"""
    case = await sanctions_service.close_case(case_id, final_decision, closed_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"case_id": str(case.case_id), "case_status": case.case_status, "final_decision": case.final_decision}


@router.post("/blocked-transactions", response_model=dict)
async def block_transaction(request: BlockTransactionRequest):
    """Block a transaction due to sanctions match"""
    blocked = await sanctions_service.block_transaction(
        transaction_id=request.transaction_id, transaction_type=request.transaction_type,
        amount=request.amount, currency=request.currency,
        originator=request.originator, originator_account=request.originator_account,
        beneficiary=request.beneficiary, beneficiary_account=request.beneficiary_account,
        blocking_reason=request.blocking_reason, list_source=request.list_source,
        matched_entry=request.matched_entry
    )
    return {"blocked_id": str(blocked.blocked_id), "transaction_id": blocked.transaction_id}


@router.get("/blocked-transactions", response_model=List[dict])
async def list_blocked_transactions(pending_release: bool = False, list_source: Optional[SanctionsList] = None):
    """List blocked transactions"""
    if pending_release:
        blocked = await sanctions_service.repository.find_blocked_pending_release()
    elif list_source:
        blocked = await sanctions_service.repository.find_blocked_by_list(list_source)
    else:
        blocked = await sanctions_service.repository.find_all_blocked()
    return [{"blocked_id": str(b.blocked_id), "transaction_id": b.transaction_id, "amount": float(b.amount), "status": b.status} for b in blocked]


@router.post("/blocked-transactions/{blocked_id}/release", response_model=dict)
async def release_transaction(blocked_id: UUID, release_authorization: str = Query(...)):
    """Release a blocked transaction"""
    blocked = await sanctions_service.release_transaction(blocked_id, release_authorization)
    if not blocked:
        raise HTTPException(status_code=404, detail="Blocked transaction not found")
    return {"blocked_id": str(blocked.blocked_id), "status": blocked.status}


@router.post("/list-updates", response_model=dict)
async def process_list_update(request: ListUpdateRequest):
    """Process a sanctions list update"""
    update = await sanctions_service.process_list_update(
        list_source=request.list_source, update_type=request.update_type,
        entries_added=request.entries_added, entries_removed=request.entries_removed,
        entries_modified=request.entries_modified, file_reference=request.file_reference,
        processed_by=request.processed_by
    )
    return {"update_id": str(update.update_id), "list_source": update.list_source.value}


@router.get("/list-updates", response_model=List[dict])
async def list_updates(list_source: Optional[SanctionsList] = None):
    """List sanctions list updates"""
    if list_source:
        updates = await sanctions_service.repository.find_list_updates_by_source(list_source)
    else:
        updates = await sanctions_service.repository.find_all_list_updates()
    return [{"update_id": str(u.update_id), "list_source": u.list_source.value, "update_date": str(u.update_date)} for u in updates]


@router.post("/reports/generate", response_model=dict)
async def generate_sanctions_report(reporting_period: str = Query(...), generated_by: str = Query(...)):
    """Generate a sanctions compliance report"""
    report = await sanctions_service.generate_report(reporting_period=reporting_period, generated_by=generated_by)
    return {"report_id": str(report.report_id), "report_date": str(report.report_date)}


@router.get("/statistics", response_model=dict)
async def get_sanctions_statistics():
    """Get sanctions compliance statistics"""
    return await sanctions_service.get_statistics()
