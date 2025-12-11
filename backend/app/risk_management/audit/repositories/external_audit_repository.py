"""External Audit Repository - Data access for external audit management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.external_audit_models import (
    ExternalAuditEngagement, PBCRequest, AuditAdjustment, ExternalAuditFinding,
    AuditOpinionLetter, ManagementRepresentationLetter
)


class ExternalAuditRepository:
    def __init__(self):
        self._engagements: Dict[UUID, ExternalAuditEngagement] = {}
        self._pbcs: Dict[UUID, PBCRequest] = {}
        self._adjustments: Dict[UUID, AuditAdjustment] = {}
        self._findings: Dict[UUID, ExternalAuditFinding] = {}
        self._opinions: Dict[UUID, AuditOpinionLetter] = {}
        self._rep_letters: Dict[UUID, ManagementRepresentationLetter] = {}

    async def save_engagement(self, engagement: ExternalAuditEngagement) -> None:
        self._engagements[engagement.engagement_id] = engagement

    async def find_engagement_by_id(self, engagement_id: UUID) -> Optional[ExternalAuditEngagement]:
        return self._engagements.get(engagement_id)

    async def find_all_engagements(self) -> List[ExternalAuditEngagement]:
        return list(self._engagements.values())

    async def find_engagements_by_year(self, fiscal_year: int) -> List[ExternalAuditEngagement]:
        return [e for e in self._engagements.values() if e.fiscal_year == fiscal_year]

    async def save_pbc(self, pbc: PBCRequest) -> None:
        self._pbcs[pbc.pbc_id] = pbc

    async def find_pbc_by_id(self, pbc_id: UUID) -> Optional[PBCRequest]:
        return self._pbcs.get(pbc_id)

    async def find_all_pbcs(self) -> List[PBCRequest]:
        return list(self._pbcs.values())

    async def find_pbcs_by_engagement(self, engagement_id: UUID) -> List[PBCRequest]:
        return [p for p in self._pbcs.values() if p.engagement_id == engagement_id]

    async def find_pending_pbcs(self) -> List[PBCRequest]:
        return [p for p in self._pbcs.values() if p.status == "pending"]

    async def save_adjustment(self, adjustment: AuditAdjustment) -> None:
        self._adjustments[adjustment.adjustment_id] = adjustment

    async def find_adjustment_by_id(self, adjustment_id: UUID) -> Optional[AuditAdjustment]:
        return self._adjustments.get(adjustment_id)

    async def find_adjustments_by_engagement(self, engagement_id: UUID) -> List[AuditAdjustment]:
        return [a for a in self._adjustments.values() if a.engagement_id == engagement_id]

    async def save_finding(self, finding: ExternalAuditFinding) -> None:
        self._findings[finding.finding_id] = finding

    async def find_finding_by_id(self, finding_id: UUID) -> Optional[ExternalAuditFinding]:
        return self._findings.get(finding_id)

    async def find_findings_by_engagement(self, engagement_id: UUID) -> List[ExternalAuditFinding]:
        return [f for f in self._findings.values() if f.engagement_id == engagement_id]

    async def find_material_weaknesses(self) -> List[ExternalAuditFinding]:
        return [f for f in self._findings.values() if f.material_weakness]

    async def save_opinion(self, opinion: AuditOpinionLetter) -> None:
        self._opinions[opinion.opinion_id] = opinion

    async def find_opinion_by_id(self, opinion_id: UUID) -> Optional[AuditOpinionLetter]:
        return self._opinions.get(opinion_id)

    async def find_opinion_by_engagement(self, engagement_id: UUID) -> Optional[AuditOpinionLetter]:
        for o in self._opinions.values():
            if o.engagement_id == engagement_id:
                return o
        return None

    async def save_rep_letter(self, letter: ManagementRepresentationLetter) -> None:
        self._rep_letters[letter.letter_id] = letter

    async def find_rep_letter_by_id(self, letter_id: UUID) -> Optional[ManagementRepresentationLetter]:
        return self._rep_letters.get(letter_id)

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_engagements": len(self._engagements),
            "active_engagements": len([e for e in self._engagements.values() if e.status == "in_progress"]),
            "total_pbcs": len(self._pbcs),
            "pending_pbcs": len([p for p in self._pbcs.values() if p.status == "pending"]),
            "total_adjustments": len(self._adjustments),
            "total_findings": len(self._findings),
            "material_weaknesses": len([f for f in self._findings.values() if f.material_weakness]),
            "total_opinions": len(self._opinions),
        }


external_audit_repository = ExternalAuditRepository()
