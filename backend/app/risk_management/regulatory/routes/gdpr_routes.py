"""GDPR Compliance API Routes"""

from typing import List, Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.gdpr_models import (
    ProcessingActivity, DataSubjectConsent, DataSubjectAccessRequest,
    DataBreach, DataProtectionImpactAssessment, LawfulBasis, DSARType, DSARStatus
)
from ..services.gdpr_service import gdpr_service

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


class ProcessingActivityRequest(BaseModel):
    activity_name: str
    processing_purpose: str
    lawful_basis: LawfulBasis
    data_categories: List[str]
    data_subjects: List[str]
    retention_period: str
    data_controller: str
    data_processor: Optional[str] = None


class ConsentRequest(BaseModel):
    data_subject_id: str
    consent_purpose: str
    consent_scope: List[str]
    collection_method: str


class DSARRequest(BaseModel):
    data_subject_id: str
    data_subject_name: str
    data_subject_email: str
    request_type: DSARType
    request_details: str


class BreachRequest(BaseModel):
    breach_description: str
    data_categories_affected: List[str]
    number_of_records: int
    discovered_by: str


class DPIARequest(BaseModel):
    project_name: str
    project_description: str
    data_processing_description: str
    necessity_assessment: str
    risk_assessment: str
    assessor: str


@router.post("/processing-activities", response_model=dict)
async def register_processing_activity(request: ProcessingActivityRequest):
    """Register a new data processing activity"""
    activity = await gdpr_service.register_processing_activity(
        activity_name=request.activity_name, processing_purpose=request.processing_purpose,
        lawful_basis=request.lawful_basis, data_categories=request.data_categories,
        data_subjects=request.data_subjects, retention_period=request.retention_period,
        data_controller=request.data_controller, data_processor=request.data_processor
    )
    return {"activity_id": str(activity.activity_id), "risk_level": activity.risk_level}


@router.get("/processing-activities", response_model=List[dict])
async def list_processing_activities(high_risk_only: bool = False):
    """List all registered processing activities"""
    if high_risk_only:
        activities = await gdpr_service.repository.find_high_risk_activities()
    else:
        activities = await gdpr_service.repository.find_all_activities()
    return [{"activity_id": str(a.activity_id), "activity_name": a.activity_name, "lawful_basis": a.lawful_basis.value} for a in activities]


@router.get("/processing-activities/{activity_id}", response_model=dict)
async def get_processing_activity(activity_id: UUID):
    """Get a specific processing activity"""
    activity = await gdpr_service.repository.find_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Processing activity not found")
    return {"activity_id": str(activity.activity_id), "activity_name": activity.activity_name, "processing_purpose": activity.processing_purpose}


@router.post("/consents", response_model=dict)
async def record_consent(request: ConsentRequest):
    """Record a data subject's consent"""
    consent = await gdpr_service.record_consent(
        data_subject_id=request.data_subject_id, consent_purpose=request.consent_purpose,
        consent_scope=request.consent_scope, collection_method=request.collection_method
    )
    return {"consent_id": str(consent.consent_id), "is_active": consent.is_active}


@router.post("/consents/{consent_id}/withdraw", response_model=dict)
async def withdraw_consent(consent_id: UUID):
    """Withdraw a previously given consent"""
    consent = await gdpr_service.withdraw_consent(consent_id)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return {"consent_id": str(consent.consent_id), "withdrawn": consent.withdrawn}


@router.get("/consents/subject/{subject_id}", response_model=List[dict])
async def get_subject_consents(subject_id: str):
    """Get all consents for a data subject"""
    consents = await gdpr_service.repository.find_consents_by_subject(subject_id)
    return [{"consent_id": str(c.consent_id), "consent_purpose": c.consent_purpose, "is_active": c.is_active} for c in consents]


@router.post("/dsar", response_model=dict)
async def submit_dsar(request: DSARRequest):
    """Submit a Data Subject Access Request"""
    dsar = await gdpr_service.create_dsar(
        data_subject_id=request.data_subject_id, data_subject_name=request.data_subject_name,
        data_subject_email=request.data_subject_email, request_type=request.request_type,
        request_details=request.request_details
    )
    return {"dsar_id": str(dsar.dsar_id), "reference_number": dsar.reference_number, "due_date": str(dsar.due_date)}


@router.post("/dsar/{dsar_id}/complete", response_model=dict)
async def complete_dsar(dsar_id: UUID, completed_by: str = Query(...), response_summary: str = Query(...)):
    """Complete a DSAR"""
    dsar = await gdpr_service.complete_dsar(dsar_id, completed_by, response_summary)
    if not dsar:
        raise HTTPException(status_code=404, detail="DSAR not found")
    return {"dsar_id": str(dsar.dsar_id), "status": dsar.status.value}


@router.get("/dsar/pending", response_model=List[dict])
async def list_pending_dsars():
    """List all pending DSARs"""
    dsars = await gdpr_service.repository.find_pending_dsars()
    return [{"dsar_id": str(d.dsar_id), "reference_number": d.reference_number, "request_type": d.request_type.value, "due_date": str(d.due_date)} for d in dsars]


@router.post("/breaches", response_model=dict)
async def report_breach(request: BreachRequest):
    """Report a data breach"""
    breach = await gdpr_service.report_breach(
        breach_description=request.breach_description, data_categories_affected=request.data_categories_affected,
        number_of_records=request.number_of_records, discovered_by=request.discovered_by
    )
    return {
        "breach_id": str(breach.breach_id),
        "breach_reference": breach.breach_reference,
        "severity": breach.severity,
        "authority_notification_required": breach.authority_notification_required,
        "notification_deadline": str(breach.notification_deadline) if breach.notification_deadline else None
    }


@router.post("/breaches/{breach_id}/notify-authority", response_model=dict)
async def notify_authority(breach_id: UUID, notification_reference: str = Query(...)):
    """Record authority notification for a breach"""
    breach = await gdpr_service.notify_authority(breach_id, notification_reference)
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
    return {"breach_id": str(breach.breach_id), "authority_notified": breach.authority_notified}


@router.get("/breaches/open", response_model=List[dict])
async def list_open_breaches():
    """List all open data breaches"""
    breaches = await gdpr_service.repository.find_open_breaches()
    return [{"breach_id": str(b.breach_id), "breach_reference": b.breach_reference, "severity": b.severity} for b in breaches]


@router.post("/dpia", response_model=dict)
async def conduct_dpia(request: DPIARequest):
    """Conduct a Data Protection Impact Assessment"""
    dpia = await gdpr_service.conduct_dpia(
        project_name=request.project_name, project_description=request.project_description,
        data_processing_description=request.data_processing_description,
        necessity_assessment=request.necessity_assessment, risk_assessment=request.risk_assessment,
        assessor=request.assessor
    )
    return {"dpia_id": str(dpia.dpia_id), "overall_risk_level": dpia.overall_risk_level, "dpo_consultation_required": dpia.dpo_consultation_required}


@router.get("/dpia/pending-review", response_model=List[dict])
async def list_pending_dpias():
    """List DPIAs pending review"""
    dpias = await gdpr_service.repository.find_dpias_pending_review()
    return [{"dpia_id": str(d.dpia_id), "project_name": d.project_name, "overall_risk_level": d.overall_risk_level} for d in dpias]


@router.post("/reports/generate", response_model=dict)
async def generate_gdpr_report(reporting_period: str = Query(...), generated_by: str = Query(...)):
    """Generate a GDPR compliance report"""
    report = await gdpr_service.generate_report(reporting_period=reporting_period, generated_by=generated_by)
    return {"report_id": str(report.report_id), "report_date": str(report.report_date)}


@router.get("/statistics", response_model=dict)
async def get_gdpr_statistics():
    """Get GDPR compliance statistics"""
    return await gdpr_service.get_statistics()
