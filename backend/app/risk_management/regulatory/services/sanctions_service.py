"""Sanctions Service - Business logic for sanctions compliance"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.sanctions_models import (
    SanctionsListEntry, ScreeningRequest, ScreeningAlert, SanctionsCase,
    BlockedTransaction, SanctionsListUpdate, SanctionsReport,
    SanctionsList, ScreeningType, AlertStatus, MatchStrength
)
from ..repositories.sanctions_repository import sanctions_repository


class SanctionsService:
    def __init__(self):
        self.repository = sanctions_repository
        self._request_counter = 0
        self._case_counter = 0

    async def screen_entity(
        self, screening_type: ScreeningType, subject_type: str, subject_name: str,
        requestor: str, lists_to_screen: List[SanctionsList], **kwargs
    ) -> ScreeningRequest:
        self._request_counter += 1
        request = ScreeningRequest(
            screening_type=screening_type, request_reference=f"SCR-{date.today().strftime('%Y%m')}-{self._request_counter:06d}",
            requestor=requestor, lists_screened=lists_to_screen, subject_type=subject_type,
            subject_name=subject_name, additional_data=kwargs
        )

        entries = await self.repository.find_all_list_entries()
        active_entries = [e for e in entries if e.is_active and e.list_source in lists_to_screen]

        matches = []
        for entry in active_entries:
            score = self._calculate_match_score(subject_name, entry.name, entry.aliases)
            if score >= Decimal("70"):
                strength = MatchStrength.EXACT if score >= 95 else MatchStrength.STRONG if score >= 85 else MatchStrength.MEDIUM
                matches.append((entry, score, strength))

        request.matches_found = len(matches)
        request.status = "completed"
        request.completed_date = datetime.utcnow()

        await self.repository.save_request(request)

        for entry, score, strength in matches:
            alert = ScreeningAlert(
                request_id=request.request_id, alert_reference=f"ALT-{self._request_counter:06d}-{len(matches)}",
                list_source=entry.list_source, list_entry_id=entry.list_entry_id, matched_name=entry.name,
                subject_name=subject_name, match_strength=strength, match_score=score, match_fields=["name"],
                sla_due_date=datetime.utcnow()
            )
            await self.repository.save_alert(alert)

        return request

    def _calculate_match_score(self, query: str, name: str, aliases: List[str]) -> Decimal:
        query_lower = query.lower()
        if query_lower == name.lower():
            return Decimal("100")
        for alias in aliases:
            if query_lower == alias.lower():
                return Decimal("95")
        if query_lower in name.lower() or name.lower() in query_lower:
            return Decimal("80")
        return Decimal("0")

    async def review_alert(
        self, alert_id: UUID, decision: str, decision_rationale: str, decided_by: str
    ) -> Optional[ScreeningAlert]:
        alert = await self.repository.find_alert_by_id(alert_id)
        if alert:
            alert.decision = decision
            alert.decision_rationale = decision_rationale
            alert.decided_by = decided_by
            alert.decision_date = datetime.utcnow()
            alert.status = AlertStatus.TRUE_MATCH if decision == "match" else AlertStatus.FALSE_POSITIVE
        return alert

    async def create_case(
        self, case_type: str, source_alert_ids: List[UUID], assigned_to: str, priority: str,
        customer_id: Optional[str] = None, transaction_ids: List[str] = None
    ) -> SanctionsCase:
        self._case_counter += 1
        case = SanctionsCase(
            case_reference=f"CASE-{date.today().strftime('%Y%m')}-{self._case_counter:05d}",
            case_type=case_type, source_alert_ids=source_alert_ids, customer_id=customer_id,
            transaction_ids=transaction_ids or [], assigned_to=assigned_to, assigned_date=datetime.utcnow(),
            priority=priority
        )
        await self.repository.save_case(case)
        return case

    async def close_case(
        self, case_id: UUID, final_decision: str, closed_by: str
    ) -> Optional[SanctionsCase]:
        case = await self.repository.find_case_by_id(case_id)
        if case:
            case.final_decision = final_decision
            case.decision_date = datetime.utcnow()
            case.closed_by = closed_by
            case.closed_date = datetime.utcnow()
            case.case_status = "closed"
        return case

    async def block_transaction(
        self, transaction_id: str, transaction_type: str, amount: Decimal, currency: str,
        originator: str, originator_account: str, beneficiary: str, beneficiary_account: str,
        blocking_reason: str, list_source: SanctionsList, matched_entry: str
    ) -> BlockedTransaction:
        blocked = BlockedTransaction(
            transaction_id=transaction_id, transaction_type=transaction_type, transaction_date=datetime.utcnow(),
            amount=amount, currency=currency, originator=originator, originator_account=originator_account,
            beneficiary=beneficiary, beneficiary_account=beneficiary_account, blocking_reason=blocking_reason,
            blocked_date=datetime.utcnow(), list_source=list_source, matched_entry=matched_entry
        )
        await self.repository.save_blocked_transaction(blocked)
        return blocked

    async def release_transaction(
        self, blocked_id: UUID, release_authorization: str
    ) -> Optional[BlockedTransaction]:
        blocked = await self.repository.find_blocked_by_id(blocked_id)
        if blocked:
            blocked.release_authorized = True
            blocked.release_authorization = release_authorization
            blocked.release_date = datetime.utcnow()
            blocked.status = "released"
        return blocked

    async def process_list_update(
        self, list_source: SanctionsList, update_type: str, entries_added: int,
        entries_removed: int, entries_modified: int, file_reference: str, processed_by: str
    ) -> SanctionsListUpdate:
        update = SanctionsListUpdate(
            list_source=list_source, update_date=date.today(), update_type=update_type,
            entries_added=entries_added, entries_removed=entries_removed, entries_modified=entries_modified,
            file_reference=file_reference, processed_date=datetime.utcnow(), processed_by=processed_by
        )
        await self.repository.save_list_update(update)
        return update

    async def generate_report(self, reporting_period: str, generated_by: str) -> SanctionsReport:
        requests = await self.repository.find_all_requests()
        alerts = await self.repository.find_all_alerts()
        blocked = await self.repository.find_all_blocked()
        cases = await self.repository.find_all_cases()

        by_type = {}
        for r in requests:
            by_type[r.screening_type.value] = by_type.get(r.screening_type.value, 0) + 1

        by_strength = {}
        for a in alerts:
            by_strength[a.match_strength.value] = by_strength.get(a.match_strength.value, 0) + 1

        true_matches = len([a for a in alerts if a.status == AlertStatus.TRUE_MATCH])
        false_positives = len([a for a in alerts if a.status == AlertStatus.FALSE_POSITIVE])

        report = SanctionsReport(
            report_date=date.today(), reporting_period=reporting_period, total_screenings=len(requests),
            screenings_by_type=by_type, total_alerts=len(alerts), alerts_by_strength=by_strength,
            true_matches=true_matches, false_positives=false_positives,
            false_positive_rate=Decimal(str(false_positives / len(alerts) * 100)) if alerts else Decimal("0"),
            blocked_transactions=len(blocked), blocked_amount=sum(b.amount for b in blocked),
            cases_opened=len([c for c in cases if c.case_status == "open"]),
            cases_closed=len([c for c in cases if c.case_status == "closed"]),
            average_resolution_time=0, escalations=0, regulatory_filings=0, list_updates_processed=0,
            generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


sanctions_service = SanctionsService()
