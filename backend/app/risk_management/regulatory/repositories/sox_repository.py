"""SOX Repository - Data access for Sarbanes-Oxley compliance"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.sox_models import (
    SOXProcess, SOXControl, SOXRisk, SOXTestPlan, SOXTestResult,
    SOXDeficiency, ManagementCertification, SOXAuditCommittee, SOXReport,
    DeficiencyType
)


class SOXRepository:
    def __init__(self):
        self._processes: Dict[UUID, SOXProcess] = {}
        self._controls: Dict[UUID, SOXControl] = {}
        self._risks: Dict[UUID, SOXRisk] = {}
        self._test_plans: Dict[UUID, SOXTestPlan] = {}
        self._test_results: Dict[UUID, SOXTestResult] = {}
        self._deficiencies: Dict[UUID, SOXDeficiency] = {}
        self._certifications: Dict[UUID, ManagementCertification] = {}
        self._audit_committees: Dict[UUID, SOXAuditCommittee] = {}
        self._reports: Dict[UUID, SOXReport] = {}

    async def save_process(self, process: SOXProcess) -> None:
        self._processes[process.process_id] = process

    async def find_process_by_id(self, process_id: UUID) -> Optional[SOXProcess]:
        return self._processes.get(process_id)

    async def find_all_processes(self) -> List[SOXProcess]:
        return list(self._processes.values())

    async def find_in_scope_processes(self) -> List[SOXProcess]:
        return [p for p in self._processes.values() if p.in_scope]

    async def find_processes_by_business_unit(self, business_unit: str) -> List[SOXProcess]:
        return [p for p in self._processes.values() if p.business_unit == business_unit]

    async def save_control(self, control: SOXControl) -> None:
        self._controls[control.control_id] = control

    async def find_control_by_id(self, control_id: UUID) -> Optional[SOXControl]:
        return self._controls.get(control_id)

    async def find_all_controls(self) -> List[SOXControl]:
        return list(self._controls.values())

    async def find_key_controls(self) -> List[SOXControl]:
        return [c for c in self._controls.values() if c.key_control]

    async def find_controls_by_process(self, process_id: UUID) -> List[SOXControl]:
        return [c for c in self._controls.values() if c.process_id == process_id]

    async def find_active_controls(self) -> List[SOXControl]:
        return [c for c in self._controls.values() if c.is_active]

    async def save_risk(self, risk: SOXRisk) -> None:
        self._risks[risk.risk_id] = risk

    async def find_risk_by_id(self, risk_id: UUID) -> Optional[SOXRisk]:
        return self._risks.get(risk_id)

    async def find_all_risks(self) -> List[SOXRisk]:
        return list(self._risks.values())

    async def find_high_risks(self) -> List[SOXRisk]:
        return [r for r in self._risks.values() if r.residual_rating == "high"]

    async def save_test_plan(self, plan: SOXTestPlan) -> None:
        self._test_plans[plan.plan_id] = plan

    async def find_test_plan_by_id(self, plan_id: UUID) -> Optional[SOXTestPlan]:
        return self._test_plans.get(plan_id)

    async def find_all_test_plans(self) -> List[SOXTestPlan]:
        return list(self._test_plans.values())

    async def find_test_plans_by_fiscal_year(self, fiscal_year: int) -> List[SOXTestPlan]:
        return [p for p in self._test_plans.values() if p.fiscal_year == fiscal_year]

    async def find_pending_test_plans(self) -> List[SOXTestPlan]:
        return [p for p in self._test_plans.values() if p.status == "pending"]

    async def save_test_result(self, result: SOXTestResult) -> None:
        self._test_results[result.result_id] = result

    async def find_test_result_by_id(self, result_id: UUID) -> Optional[SOXTestResult]:
        return self._test_results.get(result_id)

    async def find_all_test_results(self) -> List[SOXTestResult]:
        return list(self._test_results.values())

    async def find_test_results_by_control(self, control_id: UUID) -> List[SOXTestResult]:
        return [r for r in self._test_results.values() if r.control_id == control_id]

    async def find_ineffective_test_results(self) -> List[SOXTestResult]:
        return [r for r in self._test_results.values() if r.overall_conclusion == "ineffective"]

    async def save_deficiency(self, deficiency: SOXDeficiency) -> None:
        self._deficiencies[deficiency.deficiency_id] = deficiency

    async def find_deficiency_by_id(self, deficiency_id: UUID) -> Optional[SOXDeficiency]:
        return self._deficiencies.get(deficiency_id)

    async def find_all_deficiencies(self) -> List[SOXDeficiency]:
        return list(self._deficiencies.values())

    async def find_open_deficiencies(self) -> List[SOXDeficiency]:
        return [d for d in self._deficiencies.values() if d.status == "open"]

    async def find_material_weaknesses(self) -> List[SOXDeficiency]:
        return [d for d in self._deficiencies.values() if d.deficiency_type == DeficiencyType.MATERIAL_WEAKNESS]

    async def find_significant_deficiencies(self) -> List[SOXDeficiency]:
        return [d for d in self._deficiencies.values() if d.deficiency_type == DeficiencyType.SIGNIFICANT_DEFICIENCY]

    async def save_certification(self, certification: ManagementCertification) -> None:
        self._certifications[certification.certification_id] = certification

    async def find_certification_by_id(self, certification_id: UUID) -> Optional[ManagementCertification]:
        return self._certifications.get(certification_id)

    async def find_all_certifications(self) -> List[ManagementCertification]:
        return list(self._certifications.values())

    async def find_certifications_by_fiscal_year(self, fiscal_year: int) -> List[ManagementCertification]:
        return [c for c in self._certifications.values() if c.fiscal_year == fiscal_year]

    async def save_audit_committee(self, report: SOXAuditCommittee) -> None:
        self._audit_committees[report.audit_committee_id] = report

    async def find_audit_committee_by_id(self, report_id: UUID) -> Optional[SOXAuditCommittee]:
        return self._audit_committees.get(report_id)

    async def find_all_audit_committees(self) -> List[SOXAuditCommittee]:
        return list(self._audit_committees.values())

    async def save_report(self, report: SOXReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[SOXReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[SOXReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_processes": len(self._processes),
            "in_scope_processes": len([p for p in self._processes.values() if p.in_scope]),
            "total_controls": len(self._controls),
            "key_controls": len([c for c in self._controls.values() if c.key_control]),
            "total_risks": len(self._risks),
            "total_test_plans": len(self._test_plans),
            "total_test_results": len(self._test_results),
            "ineffective_results": len([r for r in self._test_results.values() if r.overall_conclusion == "ineffective"]),
            "total_deficiencies": len(self._deficiencies),
            "open_deficiencies": len([d for d in self._deficiencies.values() if d.status == "open"]),
            "material_weaknesses": len([d for d in self._deficiencies.values() if d.deficiency_type == DeficiencyType.MATERIAL_WEAKNESS]),
            "total_certifications": len(self._certifications),
            "total_reports": len(self._reports),
        }


sox_repository = SOXRepository()
