"""Reporting Service - Business logic for regulatory reporting"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.reporting_models import (
    RegulatoryReport, ReportSchedule, ReportValidation, ReportDataElement,
    ReportingException, ReportAmendment, ReportingCalendar, ReportMetrics,
    ReportFrequency, ReportStatus, Regulator
)
from ..repositories.reporting_repository import reporting_repository


class ReportingService:
    def __init__(self):
        self.repository = reporting_repository

    async def create_report(
        self, report_code: str, report_name: str, regulator: Regulator,
        frequency: ReportFrequency, reporting_period_start: date, reporting_period_end: date,
        due_date: date, entity_id: str, entity_name: str, created_by: str
    ) -> RegulatoryReport:
        report = RegulatoryReport(
            report_code=report_code, report_name=report_name, regulator=regulator, frequency=frequency,
            reporting_period_start=reporting_period_start, reporting_period_end=reporting_period_end,
            due_date=due_date, entity_id=entity_id, entity_name=entity_name, created_by=created_by
        )
        await self.repository.save_report(report)
        return report

    async def get_report(self, report_id: UUID) -> Optional[RegulatoryReport]:
        return await self.repository.find_report_by_id(report_id)

    async def submit_report(
        self, report_id: UUID, submitted_by: str, submission_reference: str
    ) -> Optional[RegulatoryReport]:
        report = await self.repository.find_report_by_id(report_id)
        if report and report.status == ReportStatus.APPROVED:
            report.status = ReportStatus.SUBMITTED
            report.submitted_by = submitted_by
            report.submission_date = datetime.utcnow()
            report.submission_reference = submission_reference
        return report

    async def approve_report(
        self, report_id: UUID, approved_by: str
    ) -> Optional[RegulatoryReport]:
        report = await self.repository.find_report_by_id(report_id)
        if report and report.status == ReportStatus.PENDING_REVIEW:
            report.status = ReportStatus.APPROVED
            report.approved_by = approved_by
            report.approval_date = datetime.utcnow()
        return report

    async def create_schedule(
        self, report_code: str, report_name: str, regulator: Regulator, frequency: ReportFrequency,
        reporting_offset_days: int, entity_id: str, owner: str, data_sources: List[str],
        next_due_date: date
    ) -> ReportSchedule:
        schedule = ReportSchedule(
            report_code=report_code, report_name=report_name, regulator=regulator, frequency=frequency,
            reporting_offset_days=reporting_offset_days, entity_id=entity_id, owner=owner,
            data_sources=data_sources, dependencies=[], next_due_date=next_due_date
        )
        await self.repository.save_schedule(schedule)
        return schedule

    async def validate_report(
        self, report_id: UUID, validation_rule_id: str, rule_description: str,
        rule_type: str, expected_value: Optional[str], actual_value: str
    ) -> ReportValidation:
        passed = expected_value is None or expected_value == actual_value
        validation = ReportValidation(
            report_id=report_id, validation_rule_id=validation_rule_id, rule_description=rule_description,
            rule_type=rule_type, expected_value=expected_value, actual_value=actual_value, passed=passed,
            severity="error" if not passed else "info", resolution_required=not passed
        )
        await self.repository.save_validation(validation)
        return validation

    async def add_data_element(
        self, report_id: UUID, element_code: str, element_name: str, schedule: str,
        line_item: str, column: str, value: str, data_type: str, source_system: str
    ) -> ReportDataElement:
        element = ReportDataElement(
            report_id=report_id, element_code=element_code, element_name=element_name, schedule=schedule,
            line_item=line_item, column=column, value=value, data_type=data_type, source_system=source_system,
            extraction_date=datetime.utcnow()
        )
        await self.repository.save_data_element(element)
        return element

    async def report_exception(
        self, report_id: UUID, exception_type: str, description: str, identified_by: str,
        impact: str, remediation_action: str, remediation_owner: str, remediation_due_date: date
    ) -> ReportingException:
        exception = ReportingException(
            report_id=report_id, exception_type=exception_type, description=description,
            identified_date=date.today(), identified_by=identified_by, impact=impact,
            remediation_action=remediation_action, remediation_owner=remediation_owner,
            remediation_due_date=remediation_due_date
        )
        await self.repository.save_exception(exception)
        return exception

    async def create_amendment(
        self, original_report_id: UUID, amended_report_id: UUID, amendment_reason: str,
        changes_summary: str, elements_changed: List[Dict[str, Any]], materiality_assessment: str,
        approved_by: str
    ) -> ReportAmendment:
        amendment = ReportAmendment(
            original_report_id=original_report_id, amended_report_id=amended_report_id,
            amendment_date=date.today(), amendment_reason=amendment_reason, changes_summary=changes_summary,
            elements_changed=elements_changed, materiality_assessment=materiality_assessment,
            approved_by=approved_by, approval_date=date.today()
        )
        await self.repository.save_amendment(amendment)
        return amendment

    async def generate_calendar(
        self, year: int, month: int, report_code: str, entity_id: str,
        period_start: date, period_end: date, internal_deadline: date,
        submission_deadline: date, assigned_to: str
    ) -> ReportingCalendar:
        calendar = ReportingCalendar(
            year=year, month=month, report_code=report_code, entity_id=entity_id,
            period_start=period_start, period_end=period_end, internal_deadline=internal_deadline,
            submission_deadline=submission_deadline, assigned_to=assigned_to
        )
        await self.repository.save_calendar(calendar)
        return calendar

    async def generate_metrics(self) -> ReportMetrics:
        reports = await self.repository.find_all_reports()
        validations = await self.repository.find_all_validations()
        exceptions = await self.repository.find_all_exceptions()

        submitted_on_time = len([r for r in reports if r.status == ReportStatus.SUBMITTED and r.submission_date and r.submission_date.date() <= r.due_date])

        metrics = ReportMetrics(
            metrics_date=date.today(), total_reports=len(reports), reports_submitted_on_time=submitted_on_time,
            reports_submitted_late=len([r for r in reports if r.status == ReportStatus.SUBMITTED]) - submitted_on_time,
            reports_rejected=len([r for r in reports if r.status == ReportStatus.REJECTED]),
            reports_amended=len([r for r in reports if r.status == ReportStatus.AMENDED]),
            validation_errors=len([v for v in validations if v.severity == "error" and not v.passed]),
            validation_warnings=len([v for v in validations if v.severity == "warning"]),
            exceptions_open=len([e for e in exceptions if e.status == "open"]),
            exceptions_resolved=len([e for e in exceptions if e.status == "resolved"]),
            automation_rate=Decimal("75"), average_preparation_days=5.0, compliance_rate=Decimal("95")
        )
        await self.repository.save_metrics(metrics)
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


reporting_service = ReportingService()
