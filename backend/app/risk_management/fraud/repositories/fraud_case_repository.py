"""Fraud Case Repository - Data access layer for fraud cases"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ..models.fraud_case_models import CaseOutcome, CasePriority, CaseStatus, FraudCase


class FraudCaseRepository:
    def __init__(self):
        self._cases: dict[UUID, FraudCase] = {}
        self._case_number_index: dict[str, UUID] = {}
        self._customer_index: dict[str, list[UUID]] = {}
        self._investigator_index: dict[str, list[UUID]] = {}

    async def save(self, case: FraudCase) -> FraudCase:
        self._cases[case.case_id] = case
        self._case_number_index[case.case_number] = case.case_id
        if case.customer_id not in self._customer_index:
            self._customer_index[case.customer_id] = []
        if case.case_id not in self._customer_index[case.customer_id]:
            self._customer_index[case.customer_id].append(case.case_id)
        if case.assigned_investigator:
            if case.assigned_investigator not in self._investigator_index:
                self._investigator_index[case.assigned_investigator] = []
            if case.case_id not in self._investigator_index[case.assigned_investigator]:
                self._investigator_index[case.assigned_investigator].append(case.case_id)
        return case

    async def find_by_id(self, case_id: UUID) -> FraudCase | None:
        return self._cases.get(case_id)

    async def find_by_number(self, case_number: str) -> FraudCase | None:
        case_id = self._case_number_index.get(case_number)
        if case_id:
            return self._cases.get(case_id)
        return None

    async def find_by_customer(self, customer_id: str, limit: int = 100) -> list[FraudCase]:
        case_ids = self._customer_index.get(customer_id, [])
        cases = [self._cases[cid] for cid in case_ids if cid in self._cases]
        return sorted(cases, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_investigator(self, investigator: str, limit: int = 100) -> list[FraudCase]:
        case_ids = self._investigator_index.get(investigator, [])
        cases = [self._cases[cid] for cid in case_ids if cid in self._cases]
        return sorted(cases, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_status(self, status: CaseStatus, limit: int = 100) -> list[FraudCase]:
        cases = [c for c in self._cases.values() if c.status == status]
        return sorted(cases, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_priority(self, priority: CasePriority, limit: int = 100) -> list[FraudCase]:
        cases = [c for c in self._cases.values() if c.priority == priority]
        return sorted(cases, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_open_cases(self, limit: int = 100) -> list[FraudCase]:
        open_statuses = [CaseStatus.OPEN, CaseStatus.UNDER_INVESTIGATION, CaseStatus.PENDING_REVIEW]
        cases = [c for c in self._cases.values() if c.status in open_statuses]
        return sorted(cases, key=lambda x: (x.priority.value, x.created_at), reverse=True)[:limit]

    async def find_overdue_cases(self, limit: int = 100) -> list[FraudCase]:
        now = datetime.now(UTC)
        overdue = [
            c for c in self._cases.values()
            if c.sla_deadline and c.sla_deadline < now
            and c.status not in [CaseStatus.CLOSED, CaseStatus.DISMISSED]
        ]
        return sorted(overdue, key=lambda x: x.sla_deadline)[:limit]

    async def find_by_outcome(self, outcome: CaseOutcome, limit: int = 100) -> list[FraudCase]:
        cases = [c for c in self._cases.values() if c.outcome == outcome]
        return sorted(cases, key=lambda x: x.closed_at or x.created_at, reverse=True)[:limit]

    async def find_unassigned(self, limit: int = 100) -> list[FraudCase]:
        unassigned = [
            c for c in self._cases.values()
            if c.assigned_investigator is None
            and c.status not in [CaseStatus.CLOSED, CaseStatus.DISMISSED]
        ]
        return sorted(unassigned, key=lambda x: x.created_at)[:limit]

    async def find_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 500) -> list[FraudCase]:
        cases = [
            c for c in self._cases.values()
            if start_date <= c.created_at <= end_date
        ]
        return sorted(cases, key=lambda x: x.created_at, reverse=True)[:limit]

    async def update(self, case: FraudCase) -> FraudCase:
        case.updated_at = datetime.now(UTC)
        self._cases[case.case_id] = case
        return case

    async def delete(self, case_id: UUID) -> bool:
        if case_id in self._cases:
            case = self._cases[case_id]
            del self._cases[case_id]
            if case.case_number in self._case_number_index:
                del self._case_number_index[case.case_number]
            return True
        return False

    async def count_by_status(self) -> dict[str, int]:
        counts = {}
        for case in self._cases.values():
            status_key = case.status.value
            counts[status_key] = counts.get(status_key, 0) + 1
        return counts

    async def get_statistics(self) -> dict[str, Any]:
        total = len(self._cases)
        open_count = len([c for c in self._cases.values() if c.status in [CaseStatus.OPEN, CaseStatus.UNDER_INVESTIGATION]])
        closed_count = len([c for c in self._cases.values() if c.status == CaseStatus.CLOSED])
        total_loss = sum(c.actual_loss for c in self._cases.values())
        total_prevented = sum(c.prevented_loss for c in self._cases.values())
        return {
            "total_cases": total,
            "open_cases": open_count,
            "closed_cases": closed_count,
            "total_loss": total_loss,
            "prevented_loss": total_prevented
        }

    async def get_all(self, limit: int = 1000, offset: int = 0) -> list[FraudCase]:
        cases = sorted(self._cases.values(), key=lambda x: x.created_at, reverse=True)
        return cases[offset:offset + limit]

    async def count(self) -> int:
        return len(self._cases)


fraud_case_repository = FraudCaseRepository()
