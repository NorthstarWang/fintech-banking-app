"""Regulatory Reporting API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.reporting_models import ReportFrequency, ReportStatus, Regulator
from ..services.reporting_service import reporting_service

router = APIRouter(prefix="/reporting", tags=["Regulatory Reporting"])


class ReportCreateRequest(BaseModel):
    report_code: str
    report_name: str
    regulator: Regulator
    frequency: ReportFrequency
    reporting_period_start: date
    reporting_period_end: date
    due_date: date
    entity_id: str
    entity_name: str
    created_by: str


class ScheduleCreateRequest(BaseModel):
    report_code: str
    report_name: str
    regulator: Regulator
    frequency: ReportFrequency
    reporting_offset_days: int
    entity_id: str
    owner: str
    data_sources: List[str]
    next_due_date: date


class ValidationRequest(BaseModel):
    report_id: UUID
    validation_rule_id: str
    rule_description: str
    rule_type: str
    expected_value: Optional[str] = None
    actual_value: str


class DataElementRequest(BaseModel):
    report_id: UUID
    element_code: str
    element_name: str
    schedule: str
    line_item: str
    column: str
    value: str
    data_type: str
    source_system: str


class ExceptionRequest(BaseModel):
    report_id: UUID
    exception_type: str
    description: str
    identified_by: str
    impact: str
    remediation_action: str
    remediation_owner: str
    remediation_due_date: date


class AmendmentRequest(BaseModel):
    original_report_id: UUID
    amended_report_id: UUID
    amendment_reason: str
    changes_summary: str
    elements_changed: List[Dict[str, Any]]
    materiality_assessment: str
    approved_by: str


class CalendarRequest(BaseModel):
    year: int
    month: int
    report_code: str
    entity_id: str
    period_start: date
    period_end: date
    internal_deadline: date
    submission_deadline: date
    assigned_to: str


@router.post("/reports", response_model=dict)
async def create_report(request: ReportCreateRequest):
    """Create a new regulatory report"""
    report = await reporting_service.create_report(
        report_code=request.report_code, report_name=request.report_name,
        regulator=request.regulator, frequency=request.frequency,
        reporting_period_start=request.reporting_period_start,
        reporting_period_end=request.reporting_period_end,
        due_date=request.due_date, entity_id=request.entity_id,
        entity_name=request.entity_name, created_by=request.created_by
    )
    return {"report_id": str(report.report_id), "status": report.status.value}


@router.get("/reports", response_model=List[dict])
async def list_reports(
    status: Optional[ReportStatus] = None,
    regulator: Optional[str] = None
):
    """List regulatory reports"""
    if status:
        reports = await reporting_service.repository.find_reports_by_status(status)
    elif regulator:
        reports = await reporting_service.repository.find_reports_by_regulator(regulator)
    else:
        reports = await reporting_service.repository.find_all_reports()
    return [{"report_id": str(r.report_id), "report_name": r.report_name, "status": r.status.value, "due_date": str(r.due_date)} for r in reports]


@router.get("/reports/{report_id}", response_model=dict)
async def get_report(report_id: UUID):
    """Get a specific regulatory report"""
    report = await reporting_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "report_id": str(report.report_id),
        "report_name": report.report_name,
        "regulator": report.regulator.value,
        "status": report.status.value,
        "due_date": str(report.due_date)
    }


@router.post("/reports/{report_id}/approve", response_model=dict)
async def approve_report(report_id: UUID, approved_by: str = Query(...)):
    """Approve a regulatory report"""
    report = await reporting_service.approve_report(report_id, approved_by)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or not pending review")
    return {"report_id": str(report.report_id), "status": report.status.value}


@router.post("/reports/{report_id}/submit", response_model=dict)
async def submit_report(
    report_id: UUID,
    submitted_by: str = Query(...),
    submission_reference: str = Query(...)
):
    """Submit a regulatory report"""
    report = await reporting_service.submit_report(report_id, submitted_by, submission_reference)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or not approved")
    return {"report_id": str(report.report_id), "status": report.status.value, "submission_reference": report.submission_reference}


@router.get("/reports/due", response_model=List[dict])
async def list_due_reports(due_by: date = Query(...)):
    """List reports due by a specific date"""
    reports = await reporting_service.repository.find_reports_due_before(due_by)
    return [{"report_id": str(r.report_id), "report_name": r.report_name, "due_date": str(r.due_date)} for r in reports]


@router.post("/schedules", response_model=dict)
async def create_schedule(request: ScheduleCreateRequest):
    """Create a reporting schedule"""
    schedule = await reporting_service.create_schedule(
        report_code=request.report_code, report_name=request.report_name,
        regulator=request.regulator, frequency=request.frequency,
        reporting_offset_days=request.reporting_offset_days, entity_id=request.entity_id,
        owner=request.owner, data_sources=request.data_sources, next_due_date=request.next_due_date
    )
    return {"schedule_id": str(schedule.schedule_id), "next_due_date": str(schedule.next_due_date)}


@router.get("/schedules", response_model=List[dict])
async def list_schedules(active_only: bool = True, regulator: Optional[str] = None):
    """List reporting schedules"""
    if regulator:
        schedules = await reporting_service.repository.find_schedules_by_regulator(regulator)
    elif active_only:
        schedules = await reporting_service.repository.find_active_schedules()
    else:
        schedules = await reporting_service.repository.find_all_schedules()
    return [{"schedule_id": str(s.schedule_id), "report_name": s.report_name, "frequency": s.frequency.value, "next_due_date": str(s.next_due_date)} for s in schedules]


@router.post("/validations", response_model=dict)
async def validate_report(request: ValidationRequest):
    """Run a validation rule on a report"""
    validation = await reporting_service.validate_report(
        report_id=request.report_id, validation_rule_id=request.validation_rule_id,
        rule_description=request.rule_description, rule_type=request.rule_type,
        expected_value=request.expected_value, actual_value=request.actual_value
    )
    return {"validation_id": str(validation.validation_id), "passed": validation.passed, "severity": validation.severity}


@router.get("/validations/{report_id}", response_model=List[dict])
async def get_report_validations(report_id: UUID):
    """Get validations for a report"""
    validations = await reporting_service.repository.find_validations_by_report(report_id)
    return [{"validation_id": str(v.validation_id), "rule_description": v.rule_description, "passed": v.passed} for v in validations]


@router.get("/validations/failed", response_model=List[dict])
async def list_failed_validations():
    """List all failed validations"""
    validations = await reporting_service.repository.find_failed_validations()
    return [{"validation_id": str(v.validation_id), "report_id": str(v.report_id), "rule_description": v.rule_description} for v in validations]


@router.post("/data-elements", response_model=dict)
async def add_data_element(request: DataElementRequest):
    """Add a data element to a report"""
    element = await reporting_service.add_data_element(
        report_id=request.report_id, element_code=request.element_code,
        element_name=request.element_name, schedule=request.schedule,
        line_item=request.line_item, column=request.column,
        value=request.value, data_type=request.data_type, source_system=request.source_system
    )
    return {"element_id": str(element.element_id), "element_code": element.element_code}


@router.get("/data-elements/{report_id}", response_model=List[dict])
async def get_report_data_elements(report_id: UUID):
    """Get data elements for a report"""
    elements = await reporting_service.repository.find_data_elements_by_report(report_id)
    return [{"element_id": str(e.element_id), "element_code": e.element_code, "value": e.value} for e in elements]


@router.post("/exceptions", response_model=dict)
async def report_exception(request: ExceptionRequest):
    """Report an exception"""
    exception = await reporting_service.report_exception(
        report_id=request.report_id, exception_type=request.exception_type,
        description=request.description, identified_by=request.identified_by,
        impact=request.impact, remediation_action=request.remediation_action,
        remediation_owner=request.remediation_owner, remediation_due_date=request.remediation_due_date
    )
    return {"exception_id": str(exception.exception_id), "status": exception.status}


@router.get("/exceptions/open", response_model=List[dict])
async def list_open_exceptions():
    """List open exceptions"""
    exceptions = await reporting_service.repository.find_open_exceptions()
    return [{"exception_id": str(e.exception_id), "exception_type": e.exception_type, "description": e.description} for e in exceptions]


@router.post("/amendments", response_model=dict)
async def create_amendment(request: AmendmentRequest):
    """Create a report amendment"""
    amendment = await reporting_service.create_amendment(
        original_report_id=request.original_report_id, amended_report_id=request.amended_report_id,
        amendment_reason=request.amendment_reason, changes_summary=request.changes_summary,
        elements_changed=request.elements_changed, materiality_assessment=request.materiality_assessment,
        approved_by=request.approved_by
    )
    return {"amendment_id": str(amendment.amendment_id)}


@router.post("/calendar", response_model=dict)
async def generate_calendar_entry(request: CalendarRequest):
    """Generate a reporting calendar entry"""
    calendar = await reporting_service.generate_calendar(
        year=request.year, month=request.month, report_code=request.report_code,
        entity_id=request.entity_id, period_start=request.period_start, period_end=request.period_end,
        internal_deadline=request.internal_deadline, submission_deadline=request.submission_deadline,
        assigned_to=request.assigned_to
    )
    return {"calendar_id": str(calendar.calendar_id)}


@router.get("/calendar/{year}/{month}", response_model=List[dict])
async def get_monthly_calendar(year: int, month: int):
    """Get reporting calendar for a month"""
    calendars = await reporting_service.repository.find_calendars_by_month(year, month)
    return [{"calendar_id": str(c.calendar_id), "report_code": c.report_code, "submission_deadline": str(c.submission_deadline)} for c in calendars]


@router.post("/metrics/generate", response_model=dict)
async def generate_metrics():
    """Generate reporting metrics"""
    metrics = await reporting_service.generate_metrics()
    return {
        "metrics_id": str(metrics.metrics_id),
        "total_reports": metrics.total_reports,
        "compliance_rate": float(metrics.compliance_rate)
    }


@router.get("/statistics", response_model=dict)
async def get_reporting_statistics():
    """Get reporting statistics"""
    return await reporting_service.get_statistics()
