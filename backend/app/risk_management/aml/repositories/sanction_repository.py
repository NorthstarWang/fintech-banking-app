"""
Sanction Repository

Data access layer for sanctions screening data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.sanction_models import (
    SanctionListEntry, SanctionListType, ScreeningResult, MatchStatus,
    BatchScreeningJob
)


class SanctionRepository:
    """Repository for sanctions data access"""

    def __init__(self):
        self._entries: Dict[UUID, SanctionListEntry] = {}
        self._results: Dict[UUID, ScreeningResult] = {}
        self._jobs: Dict[UUID, BatchScreeningJob] = {}

    async def create_entry(self, entry: SanctionListEntry) -> SanctionListEntry:
        """Create a new sanction entry"""
        self._entries[entry.entry_id] = entry
        return entry

    async def get_entry(self, entry_id: UUID) -> Optional[SanctionListEntry]:
        """Get entry by ID"""
        return self._entries.get(entry_id)

    async def update_entry(self, entry: SanctionListEntry) -> SanctionListEntry:
        """Update an entry"""
        self._entries[entry.entry_id] = entry
        return entry

    async def delete_entry(self, entry_id: UUID) -> bool:
        """Delete an entry"""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def find_by_list_type(self, list_type: SanctionListType) -> List[SanctionListEntry]:
        """Find entries by list type"""
        return [e for e in self._entries.values() if e.list_type == list_type]

    async def find_active(self) -> List[SanctionListEntry]:
        """Find active entries"""
        return [e for e in self._entries.values() if e.is_active]

    async def search_by_name(self, name: str) -> List[SanctionListEntry]:
        """Search entries by name"""
        name_lower = name.lower()
        results = []
        for entry in self._entries.values():
            if name_lower in entry.primary_name.lower():
                results.append(entry)
                continue
            if any(name_lower in alias.lower() for alias in entry.aliases):
                results.append(entry)
        return results

    async def save_result(self, result: ScreeningResult) -> ScreeningResult:
        """Save screening result"""
        self._results[result.result_id] = result
        return result

    async def get_result(self, result_id: UUID) -> Optional[ScreeningResult]:
        """Get screening result by ID"""
        return self._results.get(result_id)

    async def find_results_by_entity(self, entity_id: str) -> List[ScreeningResult]:
        """Find screening results by entity ID"""
        return [r for r in self._results.values() if r.entity_id == entity_id]

    async def find_results_with_matches(self) -> List[ScreeningResult]:
        """Find results with potential matches"""
        return [r for r in self._results.values() if r.has_matches]

    async def find_pending_reviews(self) -> List[ScreeningResult]:
        """Find results pending review"""
        return [
            r for r in self._results.values()
            if r.has_matches and r.status == MatchStatus.PENDING_REVIEW
        ]

    async def save_job(self, job: BatchScreeningJob) -> BatchScreeningJob:
        """Save batch job"""
        self._jobs[job.job_id] = job
        return job

    async def get_job(self, job_id: UUID) -> Optional[BatchScreeningJob]:
        """Get batch job by ID"""
        return self._jobs.get(job_id)

    async def find_running_jobs(self) -> List[BatchScreeningJob]:
        """Find running batch jobs"""
        return [j for j in self._jobs.values() if j.status == "running"]

    async def count_entries(self) -> int:
        """Count total entries"""
        return len(self._entries)

    async def count_by_list_type(self) -> Dict[str, int]:
        """Count entries by list type"""
        counts: Dict[str, int] = {}
        for entry in self._entries.values():
            key = entry.list_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts


# Global repository instance
sanction_repository = SanctionRepository()
