"""Compliance Testing Repository - Data access for compliance testing"""

from typing import Any
from uuid import UUID

from ..models.compliance_testing_models import (
    ComplianceException,
    ComplianceMonitoring,
    ComplianceReport,
    ComplianceTestExecution,
    ComplianceTestPlan,
    RegulatoryChange,
    TestResult,
)


class ComplianceTestingRepository:
    def __init__(self):
        self._test_plans: dict[UUID, ComplianceTestPlan] = {}
        self._executions: dict[UUID, ComplianceTestExecution] = {}
        self._exceptions: dict[UUID, ComplianceException] = {}
        self._monitoring: dict[UUID, ComplianceMonitoring] = {}
        self._regulatory_changes: dict[UUID, RegulatoryChange] = {}
        self._reports: dict[UUID, ComplianceReport] = {}

    async def save_test_plan(self, plan: ComplianceTestPlan) -> None:
        self._test_plans[plan.plan_id] = plan

    async def find_test_plan_by_id(self, plan_id: UUID) -> ComplianceTestPlan | None:
        return self._test_plans.get(plan_id)

    async def find_all_test_plans(self) -> list[ComplianceTestPlan]:
        return list(self._test_plans.values())

    async def find_pending_test_plans(self) -> list[ComplianceTestPlan]:
        return [p for p in self._test_plans.values() if p.status == "planned"]

    async def save_execution(self, execution: ComplianceTestExecution) -> None:
        self._executions[execution.execution_id] = execution

    async def find_execution_by_id(self, execution_id: UUID) -> ComplianceTestExecution | None:
        return self._executions.get(execution_id)

    async def find_all_executions(self) -> list[ComplianceTestExecution]:
        return list(self._executions.values())

    async def find_executions_by_plan(self, plan_id: UUID) -> list[ComplianceTestExecution]:
        return [e for e in self._executions.values() if e.plan_id == plan_id]

    async def find_failed_executions(self) -> list[ComplianceTestExecution]:
        return [e for e in self._executions.values() if e.test_result == TestResult.FAIL]

    async def save_exception(self, exception: ComplianceException) -> None:
        self._exceptions[exception.exception_id] = exception

    async def find_exception_by_id(self, exception_id: UUID) -> ComplianceException | None:
        return self._exceptions.get(exception_id)

    async def find_all_exceptions(self) -> list[ComplianceException]:
        return list(self._exceptions.values())

    async def find_open_exceptions(self) -> list[ComplianceException]:
        return [e for e in self._exceptions.values() if e.status == "open"]

    async def save_monitoring(self, monitoring: ComplianceMonitoring) -> None:
        self._monitoring[monitoring.monitoring_id] = monitoring

    async def find_monitoring_by_id(self, monitoring_id: UUID) -> ComplianceMonitoring | None:
        return self._monitoring.get(monitoring_id)

    async def find_all_monitoring(self) -> list[ComplianceMonitoring]:
        return list(self._monitoring.values())

    async def save_regulatory_change(self, change: RegulatoryChange) -> None:
        self._regulatory_changes[change.change_id] = change

    async def find_regulatory_change_by_id(self, change_id: UUID) -> RegulatoryChange | None:
        return self._regulatory_changes.get(change_id)

    async def find_all_regulatory_changes(self) -> list[RegulatoryChange]:
        return list(self._regulatory_changes.values())

    async def find_pending_regulatory_changes(self) -> list[RegulatoryChange]:
        return [c for c in self._regulatory_changes.values() if c.status == "identified"]

    async def save_report(self, report: ComplianceReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> ComplianceReport | None:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> list[ComplianceReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_test_plans": len(self._test_plans),
            "pending_plans": len([p for p in self._test_plans.values() if p.status == "planned"]),
            "total_executions": len(self._executions),
            "passed_tests": len([e for e in self._executions.values() if e.test_result == TestResult.PASS]),
            "failed_tests": len([e for e in self._executions.values() if e.test_result == TestResult.FAIL]),
            "total_exceptions": len(self._exceptions),
            "open_exceptions": len([e for e in self._exceptions.values() if e.status == "open"]),
            "total_monitoring": len(self._monitoring),
            "total_regulatory_changes": len(self._regulatory_changes),
            "total_reports": len(self._reports),
        }


compliance_testing_repository = ComplianceTestingRepository()
