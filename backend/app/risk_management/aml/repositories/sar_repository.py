"""
SAR Repository

Data access layer for Suspicious Activity Reports.
"""

from datetime import UTC, datetime
from uuid import UUID

from ..models.sar_models import SAR, SARStatus, SARType, SuspiciousActivityType


class SARRepository:
    """Repository for SAR data access"""

    def __init__(self):
        self._sars: dict[UUID, SAR] = {}

    async def create(self, sar: SAR) -> SAR:
        """Create a new SAR"""
        self._sars[sar.sar_id] = sar
        return sar

    async def get_by_id(self, sar_id: UUID) -> SAR | None:
        """Get SAR by ID"""
        return self._sars.get(sar_id)

    async def get_by_number(self, sar_number: str) -> SAR | None:
        """Get SAR by number"""
        for sar in self._sars.values():
            if sar.sar_number == sar_number:
                return sar
        return None

    async def update(self, sar: SAR) -> SAR:
        """Update an existing SAR"""
        self._sars[sar.sar_id] = sar
        return sar

    async def delete(self, sar_id: UUID) -> bool:
        """Delete a SAR"""
        if sar_id in self._sars:
            del self._sars[sar_id]
            return True
        return False

    async def find_by_status(self, statuses: list[SARStatus]) -> list[SAR]:
        """Find SARs by status"""
        return [s for s in self._sars.values() if s.status in statuses]

    async def find_by_type(self, sar_types: list[SARType]) -> list[SAR]:
        """Find SARs by type"""
        return [s for s in self._sars.values() if s.sar_type in sar_types]

    async def find_by_activity_type(self, activity_types: list[SuspiciousActivityType]) -> list[SAR]:
        """Find SARs by activity type"""
        return [s for s in self._sars.values() if s.primary_activity_type in activity_types]

    async def find_pending_filing(self) -> list[SAR]:
        """Find SARs pending filing"""
        return await self.find_by_status([
            SARStatus.DRAFT, SARStatus.PENDING_REVIEW, SARStatus.APPROVED
        ])

    async def find_overdue(self) -> list[SAR]:
        """Find overdue SARs"""
        now = datetime.now(UTC)
        return [
            s for s in self._sars.values()
            if (s.new_deadline or s.filing_deadline) < now
            and s.status not in [SARStatus.SUBMITTED, SARStatus.ACKNOWLEDGED]
        ]

    async def find_by_preparer(self, preparer: str) -> list[SAR]:
        """Find SARs by preparer"""
        return [s for s in self._sars.values() if s.prepared_by == preparer]

    async def find_by_case(self, case_id: UUID) -> list[SAR]:
        """Find SARs linked to a case"""
        return [s for s in self._sars.values() if case_id in s.case_ids]

    async def find_filed_in_period(
        self, start_date: datetime, end_date: datetime
    ) -> list[SAR]:
        """Find SARs filed within a period"""
        return [
            s for s in self._sars.values()
            if s.submitted_at and start_date <= s.submitted_at <= end_date
        ]

    async def count_by_status(self) -> dict[str, int]:
        """Count SARs by status"""
        counts: dict[str, int] = {}
        for sar in self._sars.values():
            key = sar.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[SAR]:
        """Get all SARs with pagination"""
        sars = list(self._sars.values())
        return sars[offset:offset + limit]

    async def count(self) -> int:
        """Count total SARs"""
        return len(self._sars)


# Global repository instance
sar_repository = SARRepository()
