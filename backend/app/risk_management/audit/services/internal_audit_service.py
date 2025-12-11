"""Internal Audit Service - Business logic for internal audit management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.internal_audit_models import (
    InternalAudit, AuditWorkpaper, AuditFinding, AuditReport, AuditFollowUp,
    AuditType, AuditStatus, FindingSeverity
)
from ..repositories.internal_audit_repository import internal_audit_repository


class InternalAuditService:
    def __init__(self):
        self.repository = internal_audit_repository
        self._audit_counter = 0
        self._finding_counter = 0

    async def create_audit(
        self, audit_name: str, audit_type: AuditType, audit_scope: str,
        audit_objectives: List[str], business_unit: str,
        audit_period_start: date, audit_period_end: date,
        planned_start_date: date, planned_end_date: date,
        lead_auditor: str, audit_team: List[str], budgeted_hours: int
    ) -> InternalAudit:
        self._audit_counter += 1
        audit = InternalAudit(
            audit_reference=f"IA-{date.today().year}-{self._audit_counter:04d}",
            audit_name=audit_name, audit_type=audit_type, audit_scope=audit_scope,
            audit_objectives=audit_objectives, business_unit=business_unit,
            audit_period_start=audit_period_start, audit_period_end=audit_period_end,
            planned_start_date=planned_start_date, planned_end_date=planned_end_date,
            lead_auditor=lead_auditor, audit_team=audit_team, budgeted_hours=budgeted_hours
        )
        await self.repository.save_audit(audit)
        return audit

    async def start_audit(self, audit_id: UUID) -> Optional[InternalAudit]:
        audit = await self.repository.find_audit_by_id(audit_id)
        if audit and audit.status == AuditStatus.PLANNED:
            audit.status = AuditStatus.IN_PROGRESS
            audit.actual_start_date = date.today()
        return audit

    async def complete_audit(self, audit_id: UUID) -> Optional[InternalAudit]:
        audit = await self.repository.find_audit_by_id(audit_id)
        if audit:
            audit.status = AuditStatus.COMPLETED
            audit.actual_end_date = date.today()
        return audit

    async def create_workpaper(
        self, audit_id: UUID, workpaper_title: str, workpaper_type: str,
        section: str, prepared_by: str, testing_objective: str,
        testing_procedure: str, sample_size: int, population_size: int
    ) -> AuditWorkpaper:
        workpaper = AuditWorkpaper(
            audit_id=audit_id, workpaper_reference=f"WP-{section}-001",
            workpaper_title=workpaper_title, workpaper_type=workpaper_type,
            section=section, prepared_by=prepared_by, prepared_date=date.today(),
            testing_objective=testing_objective, testing_procedure=testing_procedure,
            sample_size=sample_size, population_size=population_size
        )
        await self.repository.save_workpaper(workpaper)
        return workpaper

    async def create_finding(
        self, audit_id: UUID, finding_title: str, severity: FindingSeverity,
        condition: str, criteria: str, cause: str, effect: str, recommendation: str
    ) -> AuditFinding:
        self._finding_counter += 1
        finding = AuditFinding(
            audit_id=audit_id,
            finding_reference=f"F-{date.today().year}-{self._finding_counter:04d}",
            finding_title=finding_title, severity=severity, condition=condition,
            criteria=criteria, cause=cause, effect=effect, recommendation=recommendation
        )
        await self.repository.save_finding(finding)
        return finding

    async def respond_to_finding(
        self, finding_id: UUID, management_response: str, action_plan: str,
        action_owner: str, target_date: date
    ) -> Optional[AuditFinding]:
        finding = await self.repository.find_finding_by_id(finding_id)
        if finding:
            finding.management_response = management_response
            finding.action_plan = action_plan
            finding.action_owner = action_owner
            finding.target_date = target_date
        return finding

    async def create_report(
        self, audit_id: UUID, report_title: str, executive_summary: str,
        scope_summary: str, methodology_summary: str, overall_opinion: str,
        drafted_by: str
    ) -> AuditReport:
        findings = await self.repository.find_findings_by_audit(audit_id)
        findings_summary = {}
        for f in findings:
            findings_summary[f.severity.value] = findings_summary.get(f.severity.value, 0) + 1

        report = AuditReport(
            audit_id=audit_id, report_reference=f"RPT-{date.today().strftime('%Y%m%d')}",
            report_title=report_title, report_type="audit_report",
            executive_summary=executive_summary, scope_summary=scope_summary,
            methodology_summary=methodology_summary, findings_summary=findings_summary,
            overall_opinion=overall_opinion, drafted_by=drafted_by, drafted_date=date.today()
        )
        await self.repository.save_report(report)
        return report

    async def follow_up_finding(
        self, finding_id: UUID, audit_id: UUID, follow_up_by: str,
        implementation_status: str, evidence_reviewed: List[str],
        auditor_assessment: str
    ) -> AuditFollowUp:
        follow_up = AuditFollowUp(
            finding_id=finding_id, audit_id=audit_id, follow_up_date=date.today(),
            follow_up_by=follow_up_by, implementation_status=implementation_status,
            evidence_reviewed=evidence_reviewed, auditor_assessment=auditor_assessment
        )
        await self.repository.save_follow_up(follow_up)

        if implementation_status == "implemented":
            finding = await self.repository.find_finding_by_id(finding_id)
            if finding:
                finding.status = "closed"
                finding.validated = True
                finding.validation_date = date.today()
                finding.validated_by = follow_up_by

        return follow_up

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


internal_audit_service = InternalAuditService()
