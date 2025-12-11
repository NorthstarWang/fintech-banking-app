"""Control Service - Business logic for control management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.control_models import (
    Control, ControlTest, ControlException, ControlGap, ControlFramework,
    ControlMapping, ControlMetrics, ControlType, ControlNature, ControlCategory,
    ControlStatus, TestResult
)
from ..repositories.control_repository import control_repository


class ControlService:
    def __init__(self):
        self.repository = control_repository
        self._control_counter = 0

    def _generate_control_code(self, category: ControlCategory) -> str:
        self._control_counter += 1
        prefix = category.value[:4].upper()
        return f"CTRL-{prefix}-{self._control_counter:04d}"

    async def create_control(
        self,
        control_name: str,
        control_description: str,
        control_objective: str,
        control_type: ControlType,
        control_nature: ControlNature,
        control_category: ControlCategory,
        business_unit: str,
        process: str,
        owner: str,
        frequency: str,
        evidence_type: str,
        evidence_location: str,
        key_control: bool = False,
        sox_control: bool = False,
        regulatory_control: bool = False
    ) -> Control:
        control = Control(
            control_code=self._generate_control_code(control_category),
            control_name=control_name,
            control_description=control_description,
            control_objective=control_objective,
            control_type=control_type,
            control_nature=control_nature,
            control_category=control_category,
            business_unit=business_unit,
            process=process,
            owner=owner,
            frequency=frequency,
            evidence_type=evidence_type,
            evidence_location=evidence_location,
            key_control=key_control,
            sox_control=sox_control,
            regulatory_control=regulatory_control,
            automation_level=100 if control_nature == ControlNature.AUTOMATED else 0
        )

        await self.repository.save_control(control)
        return control

    async def get_control(self, control_id: UUID) -> Optional[Control]:
        return await self.repository.find_control_by_id(control_id)

    async def get_control_by_code(self, control_code: str) -> Optional[Control]:
        return await self.repository.find_control_by_code(control_code)

    async def list_controls(
        self,
        status: Optional[ControlStatus] = None,
        control_type: Optional[ControlType] = None,
        business_unit: Optional[str] = None,
        key_control: Optional[bool] = None,
        sox_control: Optional[bool] = None
    ) -> List[Control]:
        controls = await self.repository.find_all_controls()

        if status:
            controls = [c for c in controls if c.status == status]
        if control_type:
            controls = [c for c in controls if c.control_type == control_type]
        if business_unit:
            controls = [c for c in controls if c.business_unit == business_unit]
        if key_control is not None:
            controls = [c for c in controls if c.key_control == key_control]
        if sox_control is not None:
            controls = [c for c in controls if c.sox_control == sox_control]

        return controls

    async def update_control_status(
        self,
        control_id: UUID,
        new_status: ControlStatus
    ) -> Optional[Control]:
        control = await self.repository.find_control_by_id(control_id)
        if not control:
            return None

        control.status = new_status
        control.last_modified = datetime.utcnow()

        await self.repository.update_control(control)
        return control

    async def record_test(
        self,
        control_id: UUID,
        test_name: str,
        test_type: str,
        test_date: date,
        test_period_start: date,
        test_period_end: date,
        tester: str,
        sample_size: int,
        population_size: int,
        exceptions_found: int,
        test_procedure: str,
        findings: List[str] = None,
        recommendations: List[str] = None
    ) -> ControlTest:
        exception_rate = Decimal(str(exceptions_found / sample_size)) if sample_size > 0 else Decimal("0")

        if exceptions_found == 0:
            test_result = TestResult.PASS
        elif exception_rate <= Decimal("0.05"):
            test_result = TestResult.PARTIAL
        else:
            test_result = TestResult.FAIL

        test = ControlTest(
            control_id=control_id,
            test_name=test_name,
            test_type=test_type,
            test_date=test_date,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            tester=tester,
            sample_size=sample_size,
            population_size=population_size,
            exceptions_found=exceptions_found,
            exception_rate=exception_rate,
            test_result=test_result,
            test_procedure=test_procedure,
            findings=findings or [],
            recommendations=recommendations or []
        )

        await self.repository.save_test(test)

        control = await self.repository.find_control_by_id(control_id)
        if control:
            control.last_test_date = test_date
            control.next_test_date = date(test_date.year + 1, test_date.month, test_date.day)

            if test_type == "design":
                control.design_rating = test_result.value
            elif test_type == "operating effectiveness":
                control.operating_rating = test_result.value

            if control.design_rating and control.operating_rating:
                if control.design_rating == "pass" and control.operating_rating == "pass":
                    control.overall_rating = "effective"
                elif control.design_rating == "fail" or control.operating_rating == "fail":
                    control.overall_rating = "ineffective"
                else:
                    control.overall_rating = "partially_effective"

            await self.repository.update_control(control)

        return test

    async def get_control_tests(self, control_id: UUID) -> List[ControlTest]:
        return await self.repository.find_tests_by_control(control_id)

    async def record_exception(
        self,
        control_id: UUID,
        test_id: UUID,
        exception_date: date,
        exception_description: str,
        root_cause: str,
        impact: str,
        severity: str,
        remediation_action: Optional[str] = None,
        remediation_owner: Optional[str] = None,
        remediation_due_date: Optional[date] = None
    ) -> ControlException:
        exception = ControlException(
            control_id=control_id,
            test_id=test_id,
            exception_date=exception_date,
            exception_description=exception_description,
            root_cause=root_cause,
            impact=impact,
            severity=severity,
            remediation_action=remediation_action,
            remediation_owner=remediation_owner,
            remediation_due_date=remediation_due_date
        )

        await self.repository.save_exception(exception)
        return exception

    async def close_exception(
        self,
        exception_id: UUID,
        verified_by: str
    ) -> Optional[ControlException]:
        exception = await self.repository.find_exception_by_id(exception_id)
        if not exception:
            return None

        exception.remediation_status = "closed"
        exception.remediation_completed_date = date.today()
        exception.verified_by = verified_by
        exception.verification_date = date.today()

        return exception

    async def record_gap(
        self,
        gap_type: str,
        gap_description: str,
        identified_by: str,
        risk_exposure: str,
        business_unit: str,
        process: str,
        severity: str,
        remediation_plan: str,
        remediation_owner: str,
        target_remediation_date: date,
        control_id: Optional[UUID] = None
    ) -> ControlGap:
        gap = ControlGap(
            control_id=control_id,
            gap_type=gap_type,
            gap_description=gap_description,
            identified_date=date.today(),
            identified_by=identified_by,
            risk_exposure=risk_exposure,
            business_unit=business_unit,
            process=process,
            severity=severity,
            remediation_plan=remediation_plan,
            remediation_owner=remediation_owner,
            target_remediation_date=target_remediation_date
        )

        await self.repository.save_gap(gap)
        return gap

    async def close_gap(
        self,
        gap_id: UUID,
        validated_by: str
    ) -> Optional[ControlGap]:
        gap = await self.repository.find_gap_by_id(gap_id)
        if not gap:
            return None

        gap.status = "closed"
        gap.actual_remediation_date = date.today()
        gap.validated_by = validated_by
        gap.validation_date = date.today()

        return gap

    async def get_open_gaps(
        self,
        business_unit: Optional[str] = None
    ) -> List[ControlGap]:
        gaps = await self.repository.find_all_gaps()
        gaps = [g for g in gaps if g.status == "open"]

        if business_unit:
            gaps = [g for g in gaps if g.business_unit == business_unit]

        return gaps

    async def create_framework(
        self,
        framework_name: str,
        framework_version: str,
        description: str,
        issuing_body: str,
        effective_date: date,
        domains: List[str],
        total_controls: int
    ) -> ControlFramework:
        framework = ControlFramework(
            framework_name=framework_name,
            framework_version=framework_version,
            description=description,
            issuing_body=issuing_body,
            effective_date=effective_date,
            domains=domains,
            total_controls=total_controls,
            applicable_controls=0,
            implemented_controls=0,
            implementation_percentage=Decimal("0")
        )

        await self.repository.save_framework(framework)
        return framework

    async def map_control_to_framework(
        self,
        control_id: UUID,
        framework_id: UUID,
        framework_control_id: str,
        framework_control_name: str,
        mapping_status: str
    ) -> ControlMapping:
        mapping = ControlMapping(
            control_id=control_id,
            framework_id=framework_id,
            framework_control_id=framework_control_id,
            framework_control_name=framework_control_name,
            mapping_status=mapping_status,
            gap_identified=mapping_status == "not_mapped"
        )

        await self.repository.save_mapping(mapping)
        return mapping

    async def generate_metrics(
        self,
        business_unit: Optional[str] = None
    ) -> ControlMetrics:
        controls = await self.list_controls(business_unit=business_unit)

        total = len(controls)
        active = len([c for c in controls if c.status == ControlStatus.ACTIVE])
        key = len([c for c in controls if c.key_control])
        automated = len([c for c in controls if c.control_nature == ControlNature.AUTOMATED])
        manual = len([c for c in controls if c.control_nature == ControlNature.MANUAL])
        sox = len([c for c in controls if c.sox_control])

        tests = await self.repository.find_all_tests()
        if business_unit:
            control_ids = {c.control_id for c in controls}
            tests = [t for t in tests if t.control_id in control_ids]

        tested = len(set(t.control_id for t in tests))
        passed = len([t for t in tests if t.test_result == TestResult.PASS])
        failed = len([t for t in tests if t.test_result == TestResult.FAIL])

        exceptions = await self.repository.find_all_exceptions()
        if business_unit:
            exceptions = [e for e in exceptions if e.control_id in control_ids]

        gaps = await self.get_open_gaps(business_unit)
        overdue = len([g for g in gaps if g.target_remediation_date < date.today()])

        remediation_days = []
        closed_gaps = [g for g in await self.repository.find_all_gaps() if g.status == "closed"]
        for g in closed_gaps:
            if g.actual_remediation_date and g.identified_date:
                days = (g.actual_remediation_date - g.identified_date).days
                remediation_days.append(days)

        avg_remediation = sum(remediation_days) / len(remediation_days) if remediation_days else 0

        sox_effective = len([c for c in controls if c.sox_control and c.overall_rating == "effective"])

        metrics = ControlMetrics(
            metrics_date=date.today(),
            business_unit=business_unit,
            total_controls=total,
            active_controls=active,
            key_controls=key,
            automated_controls=automated,
            manual_controls=manual,
            controls_tested=tested,
            controls_passed=passed,
            controls_failed=failed,
            pass_rate=Decimal(str(passed / len(tests) * 100)) if tests else Decimal("0"),
            exception_count=len(exceptions),
            open_gaps=len(gaps),
            overdue_remediations=overdue,
            average_remediation_days=avg_remediation,
            sox_controls_count=sox,
            sox_controls_effective=sox_effective
        )

        await self.repository.save_metrics(metrics)
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


control_service = ControlService()
