"""Internal Audit Repository - Data access for internal audit management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.internal_audit_models import (
    InternalAudit, AuditWorkpaper, AuditFinding, AuditReport, AuditFollowUp,
    AuditStatus
)


class InternalAuditRepository:
    def __init__(self):
        self._audits: Dict[UUID, InternalAudit] = {}
        self._workpapers: Dict[UUID, AuditWorkpaper] = {}
        self._findings: Dict[UUID, AuditFinding] = {}
        self._reports: Dict[UUID, AuditReport] = {}
        self._follow_ups: Dict[UUID, AuditFollowUp] = {}

    async def save_audit(self, audit: InternalAudit) -> None:
        self._audits[audit.audit_id] = audit

    async def find_audit_by_id(self, audit_id: UUID) -> Optional[InternalAudit]:
        return self._audits.get(audit_id)

    async def find_all_audits(self) -> List[InternalAudit]:
        return list(self._audits.values())

    async def find_audits_by_status(self, status: AuditStatus) -> List[InternalAudit]:
        return [a for a in self._audits.values() if a.status == status]

    async def find_audits_by_business_unit(self, business_unit: str) -> List[InternalAudit]:
        return [a for a in self._audits.values() if a.business_unit == business_unit]

    async def save_workpaper(self, workpaper: AuditWorkpaper) -> None:
        self._workpapers[workpaper.workpaper_id] = workpaper

    async def find_workpaper_by_id(self, workpaper_id: UUID) -> Optional[AuditWorkpaper]:
        return self._workpapers.get(workpaper_id)

    async def find_workpapers_by_audit(self, audit_id: UUID) -> List[AuditWorkpaper]:
        return [w for w in self._workpapers.values() if w.audit_id == audit_id]

    async def save_finding(self, finding: AuditFinding) -> None:
        self._findings[finding.finding_id] = finding

    async def find_finding_by_id(self, finding_id: UUID) -> Optional[AuditFinding]:
        return self._findings.get(finding_id)

    async def find_all_findings(self) -> List[AuditFinding]:
        return list(self._findings.values())

    async def find_findings_by_audit(self, audit_id: UUID) -> List[AuditFinding]:
        return [f for f in self._findings.values() if f.audit_id == audit_id]

    async def find_open_findings(self) -> List[AuditFinding]:
        return [f for f in self._findings.values() if f.status == "open"]

    async def save_report(self, report: AuditReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[AuditReport]:
        return self._reports.get(report_id)

    async def find_reports_by_audit(self, audit_id: UUID) -> List[AuditReport]:
        return [r for r in self._reports.values() if r.audit_id == audit_id]

    async def save_follow_up(self, follow_up: AuditFollowUp) -> None:
        self._follow_ups[follow_up.follow_up_id] = follow_up

    async def find_follow_up_by_id(self, follow_up_id: UUID) -> Optional[AuditFollowUp]:
        return self._follow_ups.get(follow_up_id)

    async def find_follow_ups_by_finding(self, finding_id: UUID) -> List[AuditFollowUp]:
        return [f for f in self._follow_ups.values() if f.finding_id == finding_id]

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_audits": len(self._audits),
            "in_progress_audits": len([a for a in self._audits.values() if a.status == AuditStatus.IN_PROGRESS]),
            "completed_audits": len([a for a in self._audits.values() if a.status == AuditStatus.COMPLETED]),
            "total_workpapers": len(self._workpapers),
            "total_findings": len(self._findings),
            "open_findings": len([f for f in self._findings.values() if f.status == "open"]),
            "total_reports": len(self._reports),
            "total_follow_ups": len(self._follow_ups),
        }


internal_audit_repository = InternalAuditRepository()
