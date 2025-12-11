"""Compliance Testing Service - Business logic for compliance testing"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.compliance_testing_models import (
    ComplianceTestPlan, ComplianceTestExecution, ComplianceException,
    ComplianceMonitoring, RegulatoryChange, ComplianceReport,
    TestingType, TestResult
)
from ..repositories.compliance_testing_repository import compliance_testing_repository


class ComplianceTestingService:
    def __init__(self):
        self.repository = compliance_testing_repository
        self._plan_counter = 0
        self._exception_counter = 0

    async def create_test_plan(
        self, plan_name: str, testing_period: str, regulation: str,
        requirement_reference: str, test_objective: str, test_procedure: str,
        testing_type: TestingType, sample_methodology: str, planned_sample_size: int,
        testing_frequency: str, assigned_tester: str, planned_date: date
    ) -> ComplianceTestPlan:
        self._plan_counter += 1
        plan = ComplianceTestPlan(
            plan_reference=f"CTP-{date.today().year}-{self._plan_counter:04d}",
            plan_name=plan_name, testing_period=testing_period, regulation=regulation,
            requirement_reference=requirement_reference, test_objective=test_objective,
            test_procedure=test_procedure, testing_type=testing_type,
            sample_methodology=sample_methodology, planned_sample_size=planned_sample_size,
            testing_frequency=testing_frequency, assigned_tester=assigned_tester,
            planned_date=planned_date
        )
        await self.repository.save_test_plan(plan)
        return plan

    async def execute_test(
        self, plan_id: UUID, tester: str, population_size: int, sample_size: int,
        items_tested: int, exceptions_found: int, evidence_references: List[str],
        observations: str, conclusion: str
    ) -> ComplianceTestExecution:
        exception_rate = Decimal(str(exceptions_found / items_tested * 100)) if items_tested > 0 else Decimal("0")

        if exceptions_found == 0:
            test_result = TestResult.PASS
        elif exception_rate <= Decimal("5"):
            test_result = TestResult.PARTIAL
        else:
            test_result = TestResult.FAIL

        execution = ComplianceTestExecution(
            plan_id=plan_id, execution_date=date.today(), tester=tester,
            population_size=population_size, sample_size=sample_size,
            items_tested=items_tested, exceptions_found=exceptions_found,
            exception_rate=exception_rate, test_result=test_result,
            evidence_references=evidence_references, observations=observations,
            conclusion=conclusion
        )
        await self.repository.save_execution(execution)

        plan = await self.repository.find_test_plan_by_id(plan_id)
        if plan:
            plan.status = "completed"

        return execution

    async def record_exception(
        self, execution_id: UUID, description: str, sample_item: str,
        expected_result: str, actual_result: str, severity: str, impact: str
    ) -> ComplianceException:
        self._exception_counter += 1
        exception = ComplianceException(
            execution_id=execution_id,
            exception_reference=f"CEX-{self._exception_counter:05d}",
            description=description, sample_item=sample_item,
            expected_result=expected_result, actual_result=actual_result,
            severity=severity, impact=impact
        )
        await self.repository.save_exception(exception)
        return exception

    async def remediate_exception(
        self, exception_id: UUID, root_cause: str, remediation_action: str,
        remediation_owner: str, remediation_due_date: date
    ) -> Optional[ComplianceException]:
        exception = await self.repository.find_exception_by_id(exception_id)
        if exception:
            exception.root_cause = root_cause
            exception.remediation_action = remediation_action
            exception.remediation_owner = remediation_owner
            exception.remediation_due_date = remediation_due_date
            exception.status = "in_progress"
        return exception

    async def create_monitoring(
        self, regulation: str, monitoring_area: str, monitoring_period: str,
        metrics: List[Dict[str, Any]], thresholds: Dict[str, Decimal],
        monitoring_frequency: str, owner: str
    ) -> ComplianceMonitoring:
        monitoring = ComplianceMonitoring(
            monitoring_reference=f"MON-{date.today().strftime('%Y%m%d')}-001",
            regulation=regulation, monitoring_area=monitoring_area,
            monitoring_period=monitoring_period, metrics=metrics, thresholds=thresholds,
            monitoring_frequency=monitoring_frequency, last_monitoring_date=date.today(),
            next_monitoring_date=date.today(), owner=owner
        )
        await self.repository.save_monitoring(monitoring)
        return monitoring

    async def record_regulatory_change(
        self, regulation: str, regulator: str, change_type: str, effective_date: date,
        summary: str, detailed_description: str, impact_assessment: str,
        affected_areas: List[str], assigned_to: str, implementation_deadline: date
    ) -> RegulatoryChange:
        change = RegulatoryChange(
            change_reference=f"RC-{date.today().strftime('%Y%m%d')}-001",
            regulation=regulation, regulator=regulator, change_type=change_type,
            effective_date=effective_date, summary=summary,
            detailed_description=detailed_description, impact_assessment=impact_assessment,
            affected_areas=affected_areas, assigned_to=assigned_to,
            implementation_deadline=implementation_deadline
        )
        await self.repository.save_regulatory_change(change)
        return change

    async def generate_report(
        self, report_period: str, prepared_by: str, regulations_covered: List[str],
        key_findings: List[str], recommendations: List[str], overall_compliance_status: str
    ) -> ComplianceReport:
        executions = await self.repository.find_all_executions()
        exceptions = await self.repository.find_all_exceptions()

        passed = len([e for e in executions if e.test_result == TestResult.PASS])
        failed = len([e for e in executions if e.test_result == TestResult.FAIL])

        report = ComplianceReport(
            report_reference=f"CR-{date.today().strftime('%Y%m%d')}",
            report_period=report_period, report_date=date.today(), prepared_by=prepared_by,
            regulations_covered=regulations_covered, tests_performed=len(executions),
            tests_passed=passed, tests_failed=failed,
            pass_rate=Decimal(str(passed / len(executions) * 100)) if executions else Decimal("0"),
            exceptions_identified=len(exceptions),
            open_exceptions=len([e for e in exceptions if e.status == "open"]),
            key_findings=key_findings, recommendations=recommendations,
            overall_compliance_status=overall_compliance_status
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


compliance_testing_service = ComplianceTestingService()
