"""Sanctions Repository - Data access for sanctions compliance"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.sanctions_models import (
    SanctionsListEntry, ScreeningRequest, ScreeningAlert, SanctionsCase,
    BlockedTransaction, SanctionsListUpdate, SanctionsReport,
    SanctionsList, AlertStatus
)


class SanctionsRepository:
    def __init__(self):
        self._list_entries: Dict[UUID, SanctionsListEntry] = {}
        self._requests: Dict[UUID, ScreeningRequest] = {}
        self._alerts: Dict[UUID, ScreeningAlert] = {}
        self._cases: Dict[UUID, SanctionsCase] = {}
        self._blocked_transactions: Dict[UUID, BlockedTransaction] = {}
        self._list_updates: Dict[UUID, SanctionsListUpdate] = {}
        self._reports: Dict[UUID, SanctionsReport] = {}

    async def save_list_entry(self, entry: SanctionsListEntry) -> None:
        self._list_entries[entry.list_entry_id] = entry

    async def find_list_entry_by_id(self, entry_id: UUID) -> Optional[SanctionsListEntry]:
        return self._list_entries.get(entry_id)

    async def find_all_list_entries(self) -> List[SanctionsListEntry]:
        return list(self._list_entries.values())

    async def find_list_entries_by_source(self, source: SanctionsList) -> List[SanctionsListEntry]:
        return [e for e in self._list_entries.values() if e.list_source == source]

    async def find_active_list_entries(self) -> List[SanctionsListEntry]:
        return [e for e in self._list_entries.values() if e.is_active]

    async def search_list_entries_by_name(self, name: str) -> List[SanctionsListEntry]:
        name_lower = name.lower()
        return [e for e in self._list_entries.values() if name_lower in e.name.lower() or any(name_lower in a.lower() for a in e.aliases)]

    async def save_request(self, request: ScreeningRequest) -> None:
        self._requests[request.request_id] = request

    async def find_request_by_id(self, request_id: UUID) -> Optional[ScreeningRequest]:
        return self._requests.get(request_id)

    async def find_all_requests(self) -> List[ScreeningRequest]:
        return list(self._requests.values())

    async def find_requests_by_type(self, screening_type: str) -> List[ScreeningRequest]:
        return [r for r in self._requests.values() if r.screening_type.value == screening_type]

    async def find_requests_with_matches(self) -> List[ScreeningRequest]:
        return [r for r in self._requests.values() if r.matches_found > 0]

    async def save_alert(self, alert: ScreeningAlert) -> None:
        self._alerts[alert.alert_id] = alert

    async def find_alert_by_id(self, alert_id: UUID) -> Optional[ScreeningAlert]:
        return self._alerts.get(alert_id)

    async def find_all_alerts(self) -> List[ScreeningAlert]:
        return list(self._alerts.values())

    async def find_alerts_by_status(self, status: AlertStatus) -> List[ScreeningAlert]:
        return [a for a in self._alerts.values() if a.status == status]

    async def find_pending_alerts(self) -> List[ScreeningAlert]:
        return [a for a in self._alerts.values() if a.status == AlertStatus.PENDING_REVIEW]

    async def find_alerts_by_request(self, request_id: UUID) -> List[ScreeningAlert]:
        return [a for a in self._alerts.values() if a.request_id == request_id]

    async def save_case(self, case: SanctionsCase) -> None:
        self._cases[case.case_id] = case

    async def find_case_by_id(self, case_id: UUID) -> Optional[SanctionsCase]:
        return self._cases.get(case_id)

    async def find_all_cases(self) -> List[SanctionsCase]:
        return list(self._cases.values())

    async def find_open_cases(self) -> List[SanctionsCase]:
        return [c for c in self._cases.values() if c.case_status == "open"]

    async def find_cases_by_assignee(self, assigned_to: str) -> List[SanctionsCase]:
        return [c for c in self._cases.values() if c.assigned_to == assigned_to]

    async def save_blocked_transaction(self, blocked: BlockedTransaction) -> None:
        self._blocked_transactions[blocked.blocked_id] = blocked

    async def find_blocked_by_id(self, blocked_id: UUID) -> Optional[BlockedTransaction]:
        return self._blocked_transactions.get(blocked_id)

    async def find_all_blocked(self) -> List[BlockedTransaction]:
        return list(self._blocked_transactions.values())

    async def find_blocked_pending_release(self) -> List[BlockedTransaction]:
        return [b for b in self._blocked_transactions.values() if b.status == "blocked"]

    async def find_blocked_by_list(self, list_source: SanctionsList) -> List[BlockedTransaction]:
        return [b for b in self._blocked_transactions.values() if b.list_source == list_source]

    async def save_list_update(self, update: SanctionsListUpdate) -> None:
        self._list_updates[update.update_id] = update

    async def find_list_update_by_id(self, update_id: UUID) -> Optional[SanctionsListUpdate]:
        return self._list_updates.get(update_id)

    async def find_all_list_updates(self) -> List[SanctionsListUpdate]:
        return list(self._list_updates.values())

    async def find_list_updates_by_source(self, source: SanctionsList) -> List[SanctionsListUpdate]:
        return [u for u in self._list_updates.values() if u.list_source == source]

    async def save_report(self, report: SanctionsReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[SanctionsReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[SanctionsReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_list_entries": len(self._list_entries),
            "active_list_entries": len([e for e in self._list_entries.values() if e.is_active]),
            "total_requests": len(self._requests),
            "requests_with_matches": len([r for r in self._requests.values() if r.matches_found > 0]),
            "total_alerts": len(self._alerts),
            "pending_alerts": len([a for a in self._alerts.values() if a.status == AlertStatus.PENDING_REVIEW]),
            "total_cases": len(self._cases),
            "open_cases": len([c for c in self._cases.values() if c.case_status == "open"]),
            "blocked_transactions": len(self._blocked_transactions),
            "total_reports": len(self._reports),
        }


sanctions_repository = SanctionsRepository()
