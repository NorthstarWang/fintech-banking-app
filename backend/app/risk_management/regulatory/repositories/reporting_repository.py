"""Reporting Repository - Data access for regulatory reporting"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.reporting_models import (
    RegulatoryReport, ReportSchedule, ReportValidation, ReportDataElement,
    ReportingException, ReportAmendment, ReportingCalendar, ReportMetrics,
    ReportStatus
)


class ReportingRepository:
    def __init__(self):
        self._reports: Dict[UUID, RegulatoryReport] = {}
        self._schedules: Dict[UUID, ReportSchedule] = {}
        self._validations: Dict[UUID, ReportValidation] = {}
        self._data_elements: Dict[UUID, ReportDataElement] = {}
        self._exceptions: Dict[UUID, ReportingException] = {}
        self._amendments: Dict[UUID, ReportAmendment] = {}
        self._calendars: Dict[UUID, ReportingCalendar] = {}
        self._metrics: Dict[UUID, ReportMetrics] = {}

    async def save_report(self, report: RegulatoryReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[RegulatoryReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[RegulatoryReport]:
        return list(self._reports.values())

    async def find_reports_by_status(self, status: ReportStatus) -> List[RegulatoryReport]:
        return [r for r in self._reports.values() if r.status == status]

    async def find_reports_by_regulator(self, regulator: str) -> List[RegulatoryReport]:
        return [r for r in self._reports.values() if r.regulator.value == regulator]

    async def find_reports_due_before(self, due_date: date) -> List[RegulatoryReport]:
        return [r for r in self._reports.values() if r.due_date <= due_date and r.status not in [ReportStatus.SUBMITTED, ReportStatus.ACKNOWLEDGED]]

    async def save_schedule(self, schedule: ReportSchedule) -> None:
        self._schedules[schedule.schedule_id] = schedule

    async def find_schedule_by_id(self, schedule_id: UUID) -> Optional[ReportSchedule]:
        return self._schedules.get(schedule_id)

    async def find_all_schedules(self) -> List[ReportSchedule]:
        return list(self._schedules.values())

    async def find_active_schedules(self) -> List[ReportSchedule]:
        return [s for s in self._schedules.values() if s.is_active]

    async def find_schedules_by_regulator(self, regulator: str) -> List[ReportSchedule]:
        return [s for s in self._schedules.values() if s.regulator.value == regulator]

    async def save_validation(self, validation: ReportValidation) -> None:
        self._validations[validation.validation_id] = validation

    async def find_validation_by_id(self, validation_id: UUID) -> Optional[ReportValidation]:
        return self._validations.get(validation_id)

    async def find_all_validations(self) -> List[ReportValidation]:
        return list(self._validations.values())

    async def find_validations_by_report(self, report_id: UUID) -> List[ReportValidation]:
        return [v for v in self._validations.values() if v.report_id == report_id]

    async def find_failed_validations(self) -> List[ReportValidation]:
        return [v for v in self._validations.values() if not v.passed]

    async def save_data_element(self, element: ReportDataElement) -> None:
        self._data_elements[element.element_id] = element

    async def find_data_element_by_id(self, element_id: UUID) -> Optional[ReportDataElement]:
        return self._data_elements.get(element_id)

    async def find_all_data_elements(self) -> List[ReportDataElement]:
        return list(self._data_elements.values())

    async def find_data_elements_by_report(self, report_id: UUID) -> List[ReportDataElement]:
        return [e for e in self._data_elements.values() if e.report_id == report_id]

    async def save_exception(self, exception: ReportingException) -> None:
        self._exceptions[exception.exception_id] = exception

    async def find_exception_by_id(self, exception_id: UUID) -> Optional[ReportingException]:
        return self._exceptions.get(exception_id)

    async def find_all_exceptions(self) -> List[ReportingException]:
        return list(self._exceptions.values())

    async def find_open_exceptions(self) -> List[ReportingException]:
        return [e for e in self._exceptions.values() if e.status == "open"]

    async def find_exceptions_by_report(self, report_id: UUID) -> List[ReportingException]:
        return [e for e in self._exceptions.values() if e.report_id == report_id]

    async def save_amendment(self, amendment: ReportAmendment) -> None:
        self._amendments[amendment.amendment_id] = amendment

    async def find_amendment_by_id(self, amendment_id: UUID) -> Optional[ReportAmendment]:
        return self._amendments.get(amendment_id)

    async def find_all_amendments(self) -> List[ReportAmendment]:
        return list(self._amendments.values())

    async def find_amendments_by_original_report(self, report_id: UUID) -> List[ReportAmendment]:
        return [a for a in self._amendments.values() if a.original_report_id == report_id]

    async def save_calendar(self, calendar: ReportingCalendar) -> None:
        self._calendars[calendar.calendar_id] = calendar

    async def find_calendar_by_id(self, calendar_id: UUID) -> Optional[ReportingCalendar]:
        return self._calendars.get(calendar_id)

    async def find_all_calendars(self) -> List[ReportingCalendar]:
        return list(self._calendars.values())

    async def find_calendars_by_month(self, year: int, month: int) -> List[ReportingCalendar]:
        return [c for c in self._calendars.values() if c.year == year and c.month == month]

    async def save_metrics(self, metrics: ReportMetrics) -> None:
        self._metrics[metrics.metrics_id] = metrics

    async def find_metrics_by_id(self, metrics_id: UUID) -> Optional[ReportMetrics]:
        return self._metrics.get(metrics_id)

    async def find_all_metrics(self) -> List[ReportMetrics]:
        return list(self._metrics.values())

    async def find_latest_metrics(self) -> Optional[ReportMetrics]:
        if not self._metrics:
            return None
        return max(self._metrics.values(), key=lambda x: x.metrics_date)

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_reports": len(self._reports),
            "submitted_reports": len([r for r in self._reports.values() if r.status == ReportStatus.SUBMITTED]),
            "pending_reports": len([r for r in self._reports.values() if r.status == ReportStatus.PENDING_REVIEW]),
            "total_schedules": len(self._schedules),
            "active_schedules": len([s for s in self._schedules.values() if s.is_active]),
            "total_validations": len(self._validations),
            "failed_validations": len([v for v in self._validations.values() if not v.passed]),
            "total_exceptions": len(self._exceptions),
            "open_exceptions": len([e for e in self._exceptions.values() if e.status == "open"]),
            "total_amendments": len(self._amendments),
        }


reporting_repository = ReportingRepository()
