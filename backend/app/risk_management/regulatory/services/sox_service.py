"""SOX Service - Business logic for Sarbanes-Oxley compliance"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.sox_models import (
    SOXProcess, SOXControl, SOXRisk, SOXTestPlan, SOXTestResult,
    SOXDeficiency, ManagementCertification, SOXAuditCommittee, SOXReport,
    ControlObjective, AssertionType, DeficiencyType
)
from ..repositories.sox_repository import sox_repository


class SOXService:
    def __init__(self):
        self.repository = sox_repository
        self._process_counter = 0
        self._control_counter = 0

    async def register_process(
        self, process_name: str, process_description: str, business_unit: str, process_owner: str,
        financial_statement_areas: List[str], assertions_addressed: List[AssertionType],
        materiality_threshold: Decimal, risk_rating: str, documentation_location: str
    ) -> SOXProcess:
        self._process_counter += 1
        process = SOXProcess(
            process_code=f"PROC-{self._process_counter:04d}", process_name=process_name,
            process_description=process_description, business_unit=business_unit, process_owner=process_owner,
            financial_statement_areas=financial_statement_areas, assertions_addressed=assertions_addressed,
            materiality_threshold=materiality_threshold, risk_rating=risk_rating,
            documentation_location=documentation_location
        )
        await self.repository.save_process(process)
        return process

    async def create_control(
        self, process_id: UUID, control_name: str, control_description: str,
        control_objective: ControlObjective, assertions: List[AssertionType],
        control_type: str, control_nature: str, control_frequency: str,
        control_owner: str, performer: str, evidence_type: str, evidence_retention: str,
        key_control: bool = False
    ) -> SOXControl:
        self._control_counter += 1
        control = SOXControl(
            control_code=f"CTRL-{self._control_counter:04d}", process_id=process_id,
            control_name=control_name, control_description=control_description,
            control_objective=control_objective, assertions=assertions, control_type=control_type,
            control_nature=control_nature, control_frequency=control_frequency,
            control_owner=control_owner, performer=performer, evidence_type=evidence_type,
            evidence_retention=evidence_retention, key_control=key_control
        )
        await self.repository.save_control(control)
        return control

    async def create_test_plan(
        self, fiscal_year: int, quarter: int, control_id: UUID, test_type: str,
        planned_test_date: date, sample_size: int, selection_method: str,
        test_procedure: str, assigned_tester: str
    ) -> SOXTestPlan:
        plan = SOXTestPlan(
            fiscal_year=fiscal_year, quarter=quarter, control_id=control_id, test_type=test_type,
            planned_test_date=planned_test_date, sample_size=sample_size, selection_method=selection_method,
            test_procedure=test_procedure, assigned_tester=assigned_tester
        )
        await self.repository.save_test_plan(plan)
        return plan

    async def record_test_result(
        self, plan_id: UUID, control_id: UUID, tester: str, population_size: int,
        sample_size: int, items_tested: int, exceptions_found: int, test_evidence: List[str]
    ) -> SOXTestResult:
        exception_rate = Decimal(str(exceptions_found / items_tested)) if items_tested > 0 else Decimal("0")

        if exceptions_found == 0:
            design_conclusion = operating_conclusion = overall_conclusion = "effective"
        elif exception_rate <= Decimal("0.05"):
            design_conclusion = operating_conclusion = "effective"
            overall_conclusion = "effective_with_findings"
        else:
            design_conclusion = operating_conclusion = overall_conclusion = "ineffective"

        result = SOXTestResult(
            plan_id=plan_id, control_id=control_id, test_date=date.today(), tester=tester,
            population_size=population_size, sample_size=sample_size, items_tested=items_tested,
            exceptions_found=exceptions_found, exception_rate=exception_rate,
            design_conclusion=design_conclusion, operating_conclusion=operating_conclusion,
            overall_conclusion=overall_conclusion, test_evidence=test_evidence
        )
        await self.repository.save_test_result(result)

        if overall_conclusion == "ineffective":
            await self._create_deficiency(control_id, result.result_id, exception_rate)

        return result

    async def _create_deficiency(
        self, control_id: UUID, test_result_id: UUID, exception_rate: Decimal
    ) -> SOXDeficiency:
        if exception_rate >= Decimal("0.50"):
            deficiency_type = DeficiencyType.MATERIAL_WEAKNESS
        elif exception_rate >= Decimal("0.25"):
            deficiency_type = DeficiencyType.SIGNIFICANT_DEFICIENCY
        else:
            deficiency_type = DeficiencyType.CONTROL_DEFICIENCY

        deficiency = SOXDeficiency(
            deficiency_reference=f"DEF-{date.today().strftime('%Y%m')}-{control_id.hex[:6]}",
            control_id=control_id, test_result_id=test_result_id, deficiency_type=deficiency_type,
            deficiency_description="Control testing revealed exceptions exceeding acceptable threshold",
            root_cause="To be determined", financial_statement_impact="Under assessment",
            qualitative_factors=[], compensating_controls=[],
            remediation_plan="To be developed", remediation_owner="",
            remediation_due_date=date.today()
        )
        await self.repository.save_deficiency(deficiency)
        return deficiency

    async def close_deficiency(
        self, deficiency_id: UUID, closed_by: str
    ) -> Optional[SOXDeficiency]:
        deficiency = await self.repository.find_deficiency_by_id(deficiency_id)
        if deficiency:
            deficiency.status = "closed"
            deficiency.closed_by = closed_by
            deficiency.closed_date = date.today()
        return deficiency

    async def create_certification(
        self, fiscal_year: int, certification_type: str, certifier_name: str, certifier_title: str,
        icfr_effective: bool, material_weaknesses_exist: bool, material_weaknesses_disclosed: List[str]
    ) -> ManagementCertification:
        certification = ManagementCertification(
            fiscal_year=fiscal_year, certification_type=certification_type,
            certifier_name=certifier_name, certifier_title=certifier_title,
            certification_date=date.today(), icfr_effective=icfr_effective,
            material_weaknesses_exist=material_weaknesses_exist,
            material_weaknesses_disclosed=material_weaknesses_disclosed,
            significant_changes=False,
            certification_statement=f"Section {certification_type} Certification"
        )
        await self.repository.save_certification(certification)
        return certification

    async def generate_audit_committee_report(
        self, fiscal_year: int, quarter: int, presented_by: str
    ) -> SOXAuditCommittee:
        controls = await self.repository.find_all_controls()
        results = await self.repository.find_all_test_results()
        deficiencies = await self.repository.find_all_deficiencies()

        tested = len(set(r.control_id for r in results))
        effective = len([r for r in results if r.overall_conclusion == "effective"])

        report = SOXAuditCommittee(
            report_date=date.today(), fiscal_year=fiscal_year, quarter=quarter,
            controls_tested=tested, controls_effective=effective, controls_ineffective=tested - effective,
            deficiencies_identified=len(deficiencies),
            control_deficiencies=len([d for d in deficiencies if d.deficiency_type == DeficiencyType.CONTROL_DEFICIENCY]),
            significant_deficiencies=len([d for d in deficiencies if d.deficiency_type == DeficiencyType.SIGNIFICANT_DEFICIENCY]),
            material_weaknesses=len([d for d in deficiencies if d.deficiency_type == DeficiencyType.MATERIAL_WEAKNESS]),
            remediations_completed=len([d for d in deficiencies if d.status == "closed"]),
            remediations_in_progress=len([d for d in deficiencies if d.status == "open"]),
            key_observations=[], management_actions=[], external_auditor_findings=[],
            icfr_assessment="effective" if not any(d.deficiency_type == DeficiencyType.MATERIAL_WEAKNESS for d in deficiencies) else "ineffective",
            presented_by=presented_by, presentation_date=date.today()
        )
        await self.repository.save_audit_committee(report)
        return report

    async def generate_report(self, fiscal_year: int, generated_by: str) -> SOXReport:
        processes = await self.repository.find_all_processes()
        controls = await self.repository.find_all_controls()
        results = await self.repository.find_all_test_results()
        deficiencies = await self.repository.find_all_deficiencies()

        in_scope = len([p for p in processes if p.in_scope])
        key_controls = len([c for c in controls if c.key_control])
        tested = len(set(r.control_id for r in results))
        passed = len([r for r in results if r.overall_conclusion == "effective"])

        report = SOXReport(
            report_date=date.today(), fiscal_year=fiscal_year, report_type="annual",
            total_processes=len(processes), in_scope_processes=in_scope,
            total_controls=len(controls), key_controls=key_controls, controls_tested=tested,
            test_pass_rate=Decimal(str(passed / tested * 100)) if tested > 0 else Decimal("0"),
            deficiencies_open=len([d for d in deficiencies if d.status == "open"]),
            deficiencies_closed=len([d for d in deficiencies if d.status == "closed"]),
            material_weaknesses=len([d for d in deficiencies if d.deficiency_type == DeficiencyType.MATERIAL_WEAKNESS]),
            significant_deficiencies=len([d for d in deficiencies if d.deficiency_type == DeficiencyType.SIGNIFICANT_DEFICIENCY]),
            control_deficiencies=len([d for d in deficiencies if d.deficiency_type == DeficiencyType.CONTROL_DEFICIENCY]),
            remediation_on_track=0, remediation_overdue=0,
            certification_status="pending", generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


sox_service = SOXService()
