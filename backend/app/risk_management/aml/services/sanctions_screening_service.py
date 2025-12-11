"""
Sanctions Screening Service

Handles sanctions list screening and management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import re

from ..models.sanction_models import (
    SanctionListType, MatchStatus, EntityType, SanctionListEntry,
    ScreeningRequest, ScreeningResult, MatchDetail, MatchReview,
    SanctionAlert, BatchScreeningJob, SanctionListUpdate, WatchlistEntry
)


class SanctionsScreeningService:
    """Service for sanctions screening operations"""

    def __init__(self):
        self._sanction_entries: Dict[UUID, SanctionListEntry] = {}
        self._screening_results: Dict[UUID, ScreeningResult] = {}
        self._batch_jobs: Dict[UUID, BatchScreeningJob] = {}
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize sample sanctions list data"""
        sample_entries = [
            SanctionListEntry(
                list_type=SanctionListType.OFAC_SDN,
                list_name="OFAC SDN List",
                entity_type=EntityType.INDIVIDUAL,
                primary_name="John Smith Doe",
                aliases=["John Doe", "J. Smith", "Johnny Doe"],
                nationalities=["US", "MX"],
                sanction_programs=["SDGT", "SDNTK"],
                sanction_reasons=["Terrorism", "Narcotics Trafficking"],
                is_active=True
            ),
            SanctionListEntry(
                list_type=SanctionListType.UN_CONSOLIDATED,
                list_name="UN Consolidated List",
                entity_type=EntityType.ORGANIZATION,
                primary_name="Evil Corp Ltd",
                aliases=["Evil Corporation", "EC Holdings"],
                sanction_programs=["UN-1267"],
                sanction_reasons=["Terrorism Support"],
                is_active=True
            ),
            SanctionListEntry(
                list_type=SanctionListType.EU_CONSOLIDATED,
                list_name="EU Consolidated List",
                entity_type=EntityType.INDIVIDUAL,
                primary_name="Ivan Petrov",
                aliases=["I. Petrov", "Vanya Petrov"],
                nationalities=["RU"],
                sanction_programs=["EU-269/2014"],
                sanction_reasons=["Crimea Annexation"],
                is_active=True
            ),
        ]

        for entry in sample_entries:
            self._sanction_entries[entry.entry_id] = entry

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names using basic fuzzy matching"""
        # Normalize names
        name1_normalized = re.sub(r'[^a-z\s]', '', name1.lower())
        name2_normalized = re.sub(r'[^a-z\s]', '', name2.lower())

        # Exact match
        if name1_normalized == name2_normalized:
            return 1.0

        # Token-based matching
        tokens1 = set(name1_normalized.split())
        tokens2 = set(name2_normalized.split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        jaccard = len(intersection) / len(union)

        # Bonus for same number of tokens
        if len(tokens1) == len(tokens2):
            jaccard += 0.1

        return min(jaccard, 1.0)

    async def screen_entity(self, request: ScreeningRequest) -> ScreeningResult:
        """Screen an entity against sanctions lists"""
        result = ScreeningResult(
            request_id=request.request_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            entity_name=request.entity_name
        )

        lists_to_screen = request.lists_to_screen or list(SanctionListType)
        result.lists_screened = lists_to_screen

        matches = []
        for entry in self._sanction_entries.values():
            if entry.list_type not in lists_to_screen:
                continue

            if not entry.is_active:
                continue

            match_detail = await self._check_match(request, entry)
            if match_detail and match_detail.match_score >= request.match_threshold:
                matches.append(match_detail)

        result.matches = matches
        result.has_matches = len(matches) > 0
        result.match_count = len(matches)
        if matches:
            result.highest_match_score = max(m.match_score for m in matches)

        result.screening_date = datetime.utcnow()
        self._screening_results[result.result_id] = result

        return result

    async def _check_match(
        self, request: ScreeningRequest, entry: SanctionListEntry
    ) -> Optional[MatchDetail]:
        """Check if request entity matches a sanctions entry"""
        # Check primary name
        name_score = self._calculate_name_similarity(request.entity_name, entry.primary_name)

        # Check aliases
        alias_scores = [
            self._calculate_name_similarity(request.entity_name, alias)
            for alias in entry.aliases
        ]
        if alias_scores:
            best_alias_score = max(alias_scores)
            if best_alias_score > name_score:
                name_score = best_alias_score

        # Check request aliases against entry
        for req_alias in request.aliases:
            score = self._calculate_name_similarity(req_alias, entry.primary_name)
            if score > name_score:
                name_score = score
            for entry_alias in entry.aliases:
                score = self._calculate_name_similarity(req_alias, entry_alias)
                if score > name_score:
                    name_score = score

        # Check date of birth if available
        dob_match = False
        if request.date_of_birth and entry.date_of_birth:
            dob_match = request.date_of_birth == entry.date_of_birth

        # Check nationality
        nationality_match = bool(
            set(request.nationalities) & set(entry.nationalities)
        ) if request.nationalities and entry.nationalities else False

        # Calculate overall score
        overall_score = name_score
        if dob_match:
            overall_score = min(overall_score + 0.2, 1.0)
        if nationality_match:
            overall_score = min(overall_score + 0.1, 1.0)

        if overall_score < 0.5:
            return None

        match_type = "exact" if name_score >= 0.95 else "fuzzy" if name_score >= 0.7 else "partial"

        return MatchDetail(
            list_entry_id=entry.entry_id,
            list_type=entry.list_type,
            match_score=overall_score,
            match_algorithm="token_jaccard",
            name_match_score=name_score,
            name_match_type=match_type,
            dob_match=dob_match,
            nationality_match=nationality_match,
            matched_name=entry.primary_name,
            matched_aliases=entry.aliases,
            matched_identifiers=entry.identifiers,
            sanction_programs=entry.sanction_programs
        )

    async def batch_screen(
        self, entities: List[Dict[str, Any]], job_name: str, created_by: str
    ) -> BatchScreeningJob:
        """Start a batch screening job"""
        job = BatchScreeningJob(
            job_name=job_name,
            job_type="batch_screening",
            total_entities=len(entities),
            lists_to_screen=list(SanctionListType),
            status="pending",
            created_by=created_by
        )

        self._batch_jobs[job.job_id] = job

        # Process batch (in real implementation, this would be async)
        job.status = "running"
        job.started_at = datetime.utcnow()

        for entity in entities:
            request = ScreeningRequest(
                entity_type=EntityType(entity.get("entity_type", "individual")),
                entity_id=entity.get("entity_id"),
                entity_name=entity.get("entity_name", ""),
                aliases=entity.get("aliases", []),
                requested_by=created_by
            )

            try:
                result = await self.screen_entity(request)
                job.entities_processed += 1
                if result.has_matches:
                    job.matches_found += result.match_count
            except Exception:
                job.errors_count += 1

        job.status = "completed"
        job.completed_at = datetime.utcnow()

        return job

    async def review_match(self, review: MatchReview) -> MatchReview:
        """Review a potential sanctions match"""
        result = self._screening_results.get(review.result_id)
        if result:
            for match in result.matches:
                if match.match_id == review.match_id:
                    # Update match status based on review
                    pass

        return review

    async def get_screening_result(self, result_id: UUID) -> Optional[ScreeningResult]:
        """Get a screening result by ID"""
        return self._screening_results.get(result_id)

    async def get_batch_job(self, job_id: UUID) -> Optional[BatchScreeningJob]:
        """Get a batch job by ID"""
        return self._batch_jobs.get(job_id)

    async def get_sanction_entries(
        self, list_type: Optional[SanctionListType] = None
    ) -> List[SanctionListEntry]:
        """Get sanctions list entries"""
        entries = list(self._sanction_entries.values())
        if list_type:
            entries = [e for e in entries if e.list_type == list_type]
        return entries

    async def add_sanction_entry(self, entry: SanctionListEntry) -> SanctionListEntry:
        """Add a new sanctions list entry"""
        self._sanction_entries[entry.entry_id] = entry
        return entry

    async def update_sanction_entry(
        self, entry_id: UUID, updates: Dict[str, Any]
    ) -> Optional[SanctionListEntry]:
        """Update a sanctions list entry"""
        entry = self._sanction_entries.get(entry_id)
        if not entry:
            return None

        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.last_updated = datetime.utcnow()
        return entry

    async def import_list_update(self, update: SanctionListUpdate) -> SanctionListUpdate:
        """Import updates to a sanctions list"""
        # In real implementation, this would parse and import the list
        update.processed_at = datetime.utcnow()
        update.status = "completed"
        update.applied = True
        return update

    async def get_statistics(self) -> Dict[str, Any]:
        """Get sanctions screening statistics"""
        return {
            "total_entries": len(self._sanction_entries),
            "by_list_type": {
                lt.value: len([e for e in self._sanction_entries.values() if e.list_type == lt])
                for lt in SanctionListType
            },
            "total_screenings": len(self._screening_results),
            "total_matches": sum(r.match_count for r in self._screening_results.values()),
            "batch_jobs": len(self._batch_jobs)
        }


# Global service instance
sanctions_screening_service = SanctionsScreeningService()
