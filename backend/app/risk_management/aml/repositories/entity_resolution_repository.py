"""
Entity Resolution Repository

Data access layer for entity resolution.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.entity_resolution_models import (
    MasterEntity, SourceRecord, MatchCandidate, MergeOperation,
    SplitOperation, ResolutionJob, EntityType, ResolutionStatus
)


class EntityResolutionRepository:
    """Repository for entity resolution data access"""

    def __init__(self):
        self._master_entities: Dict[UUID, MasterEntity] = {}
        self._source_records: Dict[str, SourceRecord] = {}
        self._candidates: Dict[UUID, MatchCandidate] = {}
        self._merges: Dict[UUID, MergeOperation] = {}
        self._splits: Dict[UUID, SplitOperation] = {}
        self._jobs: Dict[UUID, ResolutionJob] = {}

    async def create_master_entity(self, entity: MasterEntity) -> MasterEntity:
        """Create a master entity"""
        self._master_entities[entity.entity_id] = entity
        return entity

    async def get_master_entity(self, entity_id: UUID) -> Optional[MasterEntity]:
        """Get master entity by ID"""
        return self._master_entities.get(entity_id)

    async def update_master_entity(self, entity: MasterEntity) -> MasterEntity:
        """Update a master entity"""
        self._master_entities[entity.entity_id] = entity
        return entity

    async def delete_master_entity(self, entity_id: UUID) -> bool:
        """Delete a master entity"""
        if entity_id in self._master_entities:
            del self._master_entities[entity_id]
            return True
        return False

    async def find_by_entity_type(self, entity_type: EntityType) -> List[MasterEntity]:
        """Find master entities by type"""
        return [e for e in self._master_entities.values() if e.entity_type == entity_type]

    async def search_by_name(self, name: str) -> List[MasterEntity]:
        """Search master entities by name"""
        name_lower = name.lower()
        results = []
        for entity in self._master_entities.values():
            if name_lower in entity.primary_name.lower():
                results.append(entity)
                continue
            if any(name_lower in v.full_name.lower() for v in entity.name_variants):
                results.append(entity)
        return results

    async def create_source_record(self, record: SourceRecord) -> SourceRecord:
        """Create a source record"""
        self._source_records[record.record_id] = record
        return record

    async def get_source_record(self, record_id: str) -> Optional[SourceRecord]:
        """Get source record by ID"""
        return self._source_records.get(record_id)

    async def update_source_record(self, record: SourceRecord) -> SourceRecord:
        """Update a source record"""
        self._source_records[record.record_id] = record
        return record

    async def find_unresolved_records(self) -> List[SourceRecord]:
        """Find unresolved source records"""
        return [
            r for r in self._source_records.values()
            if r.resolution_status == ResolutionStatus.PENDING
        ]

    async def find_records_by_master(self, master_entity_id: UUID) -> List[SourceRecord]:
        """Find source records linked to a master entity"""
        return [
            r for r in self._source_records.values()
            if r.master_entity_id == master_entity_id
        ]

    async def save_candidate(self, candidate: MatchCandidate) -> MatchCandidate:
        """Save a match candidate"""
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    async def get_candidate(self, candidate_id: UUID) -> Optional[MatchCandidate]:
        """Get match candidate by ID"""
        return self._candidates.get(candidate_id)

    async def find_pending_candidates(self) -> List[MatchCandidate]:
        """Find pending match candidates"""
        return [c for c in self._candidates.values() if c.status == "pending"]

    async def save_merge(self, merge: MergeOperation) -> MergeOperation:
        """Save a merge operation"""
        self._merges[merge.merge_id] = merge
        return merge

    async def get_merge(self, merge_id: UUID) -> Optional[MergeOperation]:
        """Get merge operation by ID"""
        return self._merges.get(merge_id)

    async def save_split(self, split: SplitOperation) -> SplitOperation:
        """Save a split operation"""
        self._splits[split.split_id] = split
        return split

    async def get_split(self, split_id: UUID) -> Optional[SplitOperation]:
        """Get split operation by ID"""
        return self._splits.get(split_id)

    async def save_job(self, job: ResolutionJob) -> ResolutionJob:
        """Save a resolution job"""
        self._jobs[job.job_id] = job
        return job

    async def get_job(self, job_id: UUID) -> Optional[ResolutionJob]:
        """Get resolution job by ID"""
        return self._jobs.get(job_id)

    async def find_running_jobs(self) -> List[ResolutionJob]:
        """Find running resolution jobs"""
        return [j for j in self._jobs.values() if j.status == "running"]

    async def count_master_entities(self) -> int:
        """Count master entities"""
        return len(self._master_entities)

    async def count_source_records(self) -> int:
        """Count source records"""
        return len(self._source_records)


# Global repository instance
entity_resolution_repository = EntityResolutionRepository()
