"""External Audit Service - Business logic for external audit management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.external_audit_models import (
    ExternalAuditEngagement, PBCRequest, AuditAdjustment, ExternalAuditFinding,
    AuditOpinionLetter, ManagementRepresentationLetter, ExternalAuditType, AuditOpinion
)
from ..repositories.external_audit_repository import external_audit_repository


class ExternalAuditService:
    def __init__(self):
        self.repository = external_audit_repository
        self._engagement_counter = 0
        self._pbc_counter = 0

    async def create_engagement(
        self, audit_firm: str, audit_type: ExternalAuditType, fiscal_year: int,
        engagement_partner: str, engagement_manager: str, engagement_letter_date: date,
        scope: str, materiality_threshold: Decimal, planned_start_date: date,
        planned_end_date: date, fee_estimate: Decimal, internal_coordinator: str
    ) -> ExternalAuditEngagement:
        self._engagement_counter += 1
        engagement = ExternalAuditEngagement(
            engagement_reference=f"EXT-{fiscal_year}-{self._engagement_counter:03d}",
            audit_firm=audit_firm, audit_type=audit_type, fiscal_year=fiscal_year,
            engagement_partner=engagement_partner, engagement_manager=engagement_manager,
            engagement_letter_date=engagement_letter_date, scope=scope,
            materiality_threshold=materiality_threshold, planned_start_date=planned_start_date,
            planned_end_date=planned_end_date, fee_estimate=fee_estimate,
            internal_coordinator=internal_coordinator
        )
        await self.repository.save_engagement(engagement)
        return engagement

    async def start_engagement(self, engagement_id: UUID) -> Optional[ExternalAuditEngagement]:
        engagement = await self.repository.find_engagement_by_id(engagement_id)
        if engagement:
            engagement.status = "in_progress"
            engagement.actual_start_date = date.today()
        return engagement

    async def create_pbc_request(
        self, engagement_id: UUID, item_description: str, category: str,
        requested_by: str, due_date: date, assigned_to: str, priority: str = "normal"
    ) -> PBCRequest:
        self._pbc_counter += 1
        pbc = PBCRequest(
            engagement_id=engagement_id, pbc_reference=f"PBC-{self._pbc_counter:05d}",
            item_description=item_description, category=category,
            requested_by=requested_by, requested_date=date.today(),
            due_date=due_date, assigned_to=assigned_to, priority=priority
        )
        await self.repository.save_pbc(pbc)
        return pbc

    async def submit_pbc(
        self, pbc_id: UUID, submitted_by: str, file_references: List[str]
    ) -> Optional[PBCRequest]:
        pbc = await self.repository.find_pbc_by_id(pbc_id)
        if pbc:
            pbc.status = "submitted"
            pbc.submitted_date = date.today()
            pbc.submitted_by = submitted_by
            pbc.file_references = file_references
        return pbc

    async def record_adjustment(
        self, engagement_id: UUID, adjustment_type: str, account_affected: str,
        debit_amount: Decimal, credit_amount: Decimal, description: str, proposed_by: str
    ) -> AuditAdjustment:
        adjustment = AuditAdjustment(
            engagement_id=engagement_id,
            adjustment_reference=f"ADJ-{date.today().strftime('%Y%m%d')}-001",
            adjustment_type=adjustment_type, account_affected=account_affected,
            debit_amount=debit_amount, credit_amount=credit_amount,
            description=description, proposed_by=proposed_by, proposed_date=date.today()
        )
        await self.repository.save_adjustment(adjustment)
        return adjustment

    async def accept_adjustment(self, adjustment_id: UUID) -> Optional[AuditAdjustment]:
        adjustment = await self.repository.find_adjustment_by_id(adjustment_id)
        if adjustment:
            adjustment.management_accepted = True
            adjustment.acceptance_date = date.today()
        return adjustment

    async def record_finding(
        self, engagement_id: UUID, finding_type: str, description: str, severity: str,
        management_letter_item: bool = False, significant_deficiency: bool = False,
        material_weakness: bool = False
    ) -> ExternalAuditFinding:
        finding = ExternalAuditFinding(
            engagement_id=engagement_id,
            finding_reference=f"EF-{date.today().strftime('%Y%m')}-001",
            finding_type=finding_type, description=description, severity=severity,
            management_letter_item=management_letter_item,
            significant_deficiency=significant_deficiency, material_weakness=material_weakness
        )
        await self.repository.save_finding(finding)
        return finding

    async def issue_opinion(
        self, engagement_id: UUID, opinion_type: AuditOpinion, basis_for_opinion: str,
        signed_by: str, firm_name: str, going_concern_doubt: bool = False
    ) -> AuditOpinionLetter:
        opinion = AuditOpinionLetter(
            engagement_id=engagement_id, opinion_type=opinion_type,
            opinion_date=date.today(), report_date=date.today(),
            basis_for_opinion=basis_for_opinion, signed_by=signed_by,
            firm_name=firm_name, going_concern_doubt=going_concern_doubt
        )
        await self.repository.save_opinion(opinion)

        engagement = await self.repository.find_engagement_by_id(engagement_id)
        if engagement:
            engagement.status = "completed"
            engagement.actual_end_date = date.today()

        return opinion

    async def create_rep_letter(
        self, engagement_id: UUID, fiscal_year_end: date, representations: List[Dict[str, Any]],
        signed_by_ceo: str, signed_by_cfo: str
    ) -> ManagementRepresentationLetter:
        letter = ManagementRepresentationLetter(
            engagement_id=engagement_id, letter_date=date.today(),
            fiscal_year_end=fiscal_year_end, representations=representations,
            signed_by_ceo=signed_by_ceo, signed_by_cfo=signed_by_cfo
        )
        await self.repository.save_rep_letter(letter)
        return letter

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


external_audit_service = ExternalAuditService()
