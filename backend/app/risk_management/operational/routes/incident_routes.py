"""Incident Routes - API endpoints for operational incident management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel
from decimal import Decimal
from ..models.incident_models import (
    Incident, IncidentTimeline, IncidentEscalation, IncidentRootCauseAnalysis,
    IncidentCorrectiveAction, IncidentReport, IncidentSeverity, IncidentStatus,
    IncidentCategory, IncidentImpact
)
from ..services.incident_service import incident_service

router = APIRouter(prefix="/incidents", tags=["Operational Incidents"])


class CreateIncidentRequest(BaseModel):
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    reported_by: str
    occurred_date: datetime
    detected_date: datetime
    business_unit: str
    affected_systems: Optional[List[str]] = None
    impact_types: Optional[List[IncidentImpact]] = None
    estimated_loss: Optional[Decimal] = None


class UpdateStatusRequest(BaseModel):
    new_status: IncidentStatus
    updated_by: str
    notes: Optional[str] = None


class AssignRequest(BaseModel):
    assigned_to: str
    assigned_by: str


class EscalateRequest(BaseModel):
    escalated_to: str
    escalated_by: str
    reason: str


class RCARequest(BaseModel):
    analyst: str
    root_causes: List[str]
    contributing_factors: List[str]
    methodology: str
    findings: str
    recommendations: List[str]
    preventive_measures: List[str]


class CorrectiveActionRequest(BaseModel):
    action_type: str
    description: str
    assigned_to: str
    due_date: date
    analysis_id: Optional[UUID] = None


@router.post("/", response_model=Incident)
async def create_incident(request: CreateIncidentRequest):
    """Create new operational incident"""
    return await incident_service.create_incident(
        title=request.title,
        description=request.description,
        category=request.category,
        severity=request.severity,
        reported_by=request.reported_by,
        occurred_date=request.occurred_date,
        detected_date=request.detected_date,
        business_unit=request.business_unit,
        affected_systems=request.affected_systems,
        impact_types=request.impact_types,
        estimated_loss=request.estimated_loss
    )


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: UUID):
    """Get incident by ID"""
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/number/{incident_number}", response_model=Incident)
async def get_incident_by_number(incident_number: str):
    """Get incident by number"""
    incident = await incident_service.get_incident_by_number(incident_number)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/", response_model=List[Incident])
async def list_incidents(
    status: Optional[IncidentStatus] = Query(None),
    severity: Optional[IncidentSeverity] = Query(None),
    category: Optional[IncidentCategory] = Query(None),
    business_unit: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """List incidents with filters"""
    return await incident_service.list_incidents(
        status, severity, category, business_unit, start_date, end_date
    )


@router.put("/{incident_id}/status", response_model=Incident)
async def update_status(incident_id: UUID, request: UpdateStatusRequest):
    """Update incident status"""
    incident = await incident_service.update_incident_status(
        incident_id, request.new_status, request.updated_by, request.notes
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/{incident_id}/assign", response_model=Incident)
async def assign_incident(incident_id: UUID, request: AssignRequest):
    """Assign incident to handler"""
    incident = await incident_service.assign_incident(
        incident_id, request.assigned_to, request.assigned_by
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/escalate", response_model=IncidentEscalation)
async def escalate_incident(incident_id: UUID, request: EscalateRequest):
    """Escalate incident"""
    escalation = await incident_service.escalate_incident(
        incident_id, request.escalated_to, request.escalated_by, request.reason
    )
    if not escalation:
        raise HTTPException(status_code=404, detail="Incident not found")
    return escalation


@router.post("/{incident_id}/rca", response_model=IncidentRootCauseAnalysis)
async def add_rca(incident_id: UUID, request: RCARequest):
    """Add root cause analysis"""
    return await incident_service.add_root_cause_analysis(
        incident_id=incident_id,
        analyst=request.analyst,
        root_causes=request.root_causes,
        contributing_factors=request.contributing_factors,
        methodology=request.methodology,
        findings=request.findings,
        recommendations=request.recommendations,
        preventive_measures=request.preventive_measures
    )


@router.post("/{incident_id}/actions", response_model=IncidentCorrectiveAction)
async def add_corrective_action(incident_id: UUID, request: CorrectiveActionRequest):
    """Add corrective action"""
    return await incident_service.add_corrective_action(
        incident_id=incident_id,
        action_type=request.action_type,
        description=request.description,
        assigned_to=request.assigned_to,
        due_date=request.due_date,
        analysis_id=request.analysis_id
    )


@router.put("/actions/{action_id}/complete")
async def complete_action(action_id: UUID, verified_by: str):
    """Complete corrective action"""
    action = await incident_service.complete_corrective_action(action_id, verified_by)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.get("/{incident_id}/timeline", response_model=List[IncidentTimeline])
async def get_timeline(incident_id: UUID):
    """Get incident timeline"""
    return await incident_service.get_incident_timeline(incident_id)


@router.post("/reports", response_model=IncidentReport)
async def generate_report(
    report_type: str,
    period_start: date,
    period_end: date,
    generated_by: str
):
    """Generate incident report"""
    return await incident_service.generate_report(
        report_type, period_start, period_end, generated_by
    )


@router.get("/statistics/summary")
async def get_statistics():
    """Get incident statistics"""
    return await incident_service.get_statistics()
