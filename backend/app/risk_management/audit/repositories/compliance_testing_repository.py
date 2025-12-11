"""Compliance Testing Repository - Data access for compliance testing"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.compliance_testing_models import (
    ComplianceTestPlan, ComplianceTestExecution, ComplianceException,
    ComplianceMonitoring, RegulatoryChange, ComplianceReport, TestResult
)


class ComplianceTestingRepository:
    def __init__(self):
        self._test_plans: Dict[UUID, ComplianceTestPlan] = {}
        self._executions: Dict[UUID, ComplianceTestExecution] = {}
        self._exceptions: Dict[UUID, ComplianceException] = {}
        self._monitoring: Dict[UUID, ComplianceMonitoring] = {}
        self._regulatory_changes: Dict[UUID, RegulatoryChange] = {}
        self._reports: Dict[UUID, ComplianceReport] = {}

    async def save_test_plan(self, plan: ComplianceTestPlan) -> None:
        self._test_plans[plan.plan_id] = plan

    async def find_test_plan_by_id(self, plan_id: UUID) -> Optional[ComplianceTestPlan]:
        return self._test_plans.get(plan_id)

    async def find_all_test_plans(self) -> List[ComplianceTestPlan]:
        return list(self._test_plans.values())

    async def find_pending_test_plans(self) -> List[ComplianceTestPlan]:
        return [p for p in self._test_plans.values() if p.status == "planned"]

    async def save_execution(self, execution: ComplianceTestExecution) -> None:
        self._executions[execution.execution_id] = execution

    async def find_execution_by_id(self, execution_id: UUID) -> Optional[ComplianceTestExecution]:
        return self._executions.get(execution_id)

    async def find_all_executions(self) -> List[ComplianceTestExecution]:
        return list(self._executions.values())

    async def find_executions_by_plan(self, plan_id: UUID) -> List[ComplianceTestExecution]:
        return [e for e in self._executions.values() if e.plan_id == plan_id]

    async def find_failed_executions(self) -> List[ComplianceTestExecution]:
        return [e for e in self._executions.values() if e.test_result == TestResult.FAIL]

    async def save_exception(self, exception: ComplianceException) -> None:
        self._exceptions[exception.exception_id] = exception

    async def find_exception_by_id(self, exception_id: UUID) -> Optional[ComplianceException]:
        return self._exceptions.get(exception_id)

    async def find_all_exceptions(self) -> List[ComplianceException]:
        return list(self._exceptions.values())

    async def find_open_exceptions(self) -> List[ComplianceException]:
        return [e for e in self._exceptions.values() if e.status == "open"]

    async def save_monitoring(self, monitoring: ComplianceMonitoring) -> None:
        self._monitoring[monitoring.monitoring_id] = monitoring

    async def find_monitoring_by_id(self, monitoring_id: UUID) -> Optional[ComplianceMonitoring]:
        return self._monitoring.get(monitoring_id)

    async def find_all_monitoring(self) -> List[ComplianceMonitoring]:
        return list(self._monitoring.values())

    async def save_regulatory_change(self, change: RegulatoryChange) -> None:
        self._regulatory_changes[change.change_id] = change

    async def find_regulatory_change_by_id(self, change_id: UUID) -> Optional[RegulatoryChange]:
        return self._regulatory_changes.get(change_id)

    async def find_all_regulatory_changes(self) -> List[RegulatoryChange]:
        return list(self._regulatory_changes.values())

    async def find_pending_regulatory_changes(self) -> List[RegulatoryChange]:
        return [c for c in self._regulatory_changes.values() if c.status == "identified"]

    async def save_report(self, report: ComplianceReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[ComplianceReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[ComplianceReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> Dict[str, Any]:
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
