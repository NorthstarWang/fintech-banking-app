"""
Case Repository

Data access layer for AML investigation cases.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.case_models import AMLCase, CaseStatus, CasePriority, CaseCategory


class CaseRepository:
    """Repository for AML case data access"""

    def __init__(self):
        self._cases: Dict[UUID, AMLCase] = {}

    async def create(self, case: AMLCase) -> AMLCase:
        """Create a new case"""
        self._cases[case.case_id] = case
        return case

    async def get_by_id(self, case_id: UUID) -> Optional[AMLCase]:
        """Get case by ID"""
        return self._cases.get(case_id)

    async def get_by_number(self, case_number: str) -> Optional[AMLCase]:
        """Get case by case number"""
        for case in self._cases.values():
            if case.case_number == case_number:
                return case
        return None

    async def update(self, case: AMLCase) -> AMLCase:
        """Update an existing case"""
        self._cases[case.case_id] = case
        return case

    async def delete(self, case_id: UUID) -> bool:
        """Delete a case"""
        if case_id in self._cases:
            del self._cases[case_id]
            return True
        return False

    async def find_by_subject(self, subject_id: str) -> List[AMLCase]:
        """Find cases by primary subject"""
        return [c for c in self._cases.values() if c.primary_subject_id == subject_id]

    async def find_by_status(self, statuses: List[CaseStatus]) -> List[AMLCase]:
        """Find cases by status"""
        return [c for c in self._cases.values() if c.status in statuses]

    async def find_by_priority(self, priorities: List[CasePriority]) -> List[AMLCase]:
        """Find cases by priority"""
        return [c for c in self._cases.values() if c.priority in priorities]

    async def find_by_category(self, categories: List[CaseCategory]) -> List[AMLCase]:
        """Find cases by category"""
        return [c for c in self._cases.values() if c.category in categories]

    async def find_by_investigator(self, investigator: str) -> List[AMLCase]:
        """Find cases by lead investigator"""
        return [c for c in self._cases.values() if c.lead_investigator == investigator]

    async def find_requiring_sar(self) -> List[AMLCase]:
        """Find cases requiring SAR filing"""
        return [c for c in self._cases.values() if c.sar_required]

    async def find_overdue(self) -> List[AMLCase]:
        """Find overdue cases"""
        now = datetime.utcnow()
        return [
            c for c in self._cases.values()
            if c.due_date and c.due_date < now and c.status not in [
                CaseStatus.CLOSED_NO_ACTION,
                CaseStatus.CLOSED_WITH_ACTION
            ]
        ]

    async def find_open(self) -> List[AMLCase]:
        """Find open cases"""
        open_statuses = [
            CaseStatus.DRAFT, CaseStatus.OPEN, CaseStatus.IN_PROGRESS,
            CaseStatus.PENDING_REVIEW, CaseStatus.ESCALATED
        ]
        return await self.find_by_status(open_statuses)

    async def count_by_status(self) -> Dict[str, int]:
        """Count cases by status"""
        counts: Dict[str, int] = {}
        for case in self._cases.values():
            key = case.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[AMLCase]:
        """Get all cases with pagination"""
        cases = list(self._cases.values())
        return cases[offset:offset + limit]

    async def count(self) -> int:
        """Count total cases"""
        return len(self._cases)


# Global repository instance
case_repository = CaseRepository()
