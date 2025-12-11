"""
Entity Resolution Service

Handles entity resolution, deduplication, and golden record management.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from uuid import UUID, uuid4
from collections import defaultdict
import re

from ..models.entity_resolution_models import (
    EntityType, MatchConfidence, ResolutionStatus, IdentityAttribute,
    NameVariant, AddressRecord, IdentifierRecord, RelationshipRecord,
    MasterEntity, SourceRecord, MatchCandidate, MergeOperation, SplitOperation,
    ResolutionRule, ResolutionJob, EntityResolutionStatistics
)


class EntityResolutionService:
    """Service for entity resolution and identity management"""

    def __init__(self):
        self._master_entities: Dict[UUID, MasterEntity] = {}
        self._source_records: Dict[str, SourceRecord] = {}
        self._match_candidates: Dict[UUID, MatchCandidate] = {}
        self._merge_operations: Dict[UUID, MergeOperation] = {}
        self._resolution_rules: Dict[UUID, ResolutionRule] = {}
        self._jobs: Dict[UUID, ResolutionJob] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default resolution rules"""
        default_rules = [
            ResolutionRule(
                rule_name="Exact SSN Match",
                rule_code="SSN_EXACT",
                entity_type=EntityType.INDIVIDUAL,
                match_fields=["ssn"],
                field_weights={"ssn": 1.0},
                threshold=1.0,
                auto_merge_threshold=1.0,
                auto_merge_enabled=True,
                is_active=True,
                priority=1,
                created_by="system"
            ),
            ResolutionRule(
                rule_name="Name + DOB Match",
                rule_code="NAME_DOB",
                entity_type=EntityType.INDIVIDUAL,
                match_fields=["name", "date_of_birth"],
                field_weights={"name": 0.6, "date_of_birth": 0.4},
                threshold=0.85,
                auto_merge_threshold=0.98,
                auto_merge_enabled=True,
                is_active=True,
                priority=2,
                created_by="system"
            ),
            ResolutionRule(
                rule_name="Name + Address Match",
                rule_code="NAME_ADDR",
                entity_type=EntityType.INDIVIDUAL,
                match_fields=["name", "address"],
                field_weights={"name": 0.5, "address": 0.5},
                threshold=0.80,
                auto_merge_threshold=0.95,
                auto_merge_enabled=True,
                is_active=True,
                priority=3,
                created_by="system"
            ),
            ResolutionRule(
                rule_name="Company Registration Match",
                rule_code="COMPANY_REG",
                entity_type=EntityType.ORGANIZATION,
                match_fields=["registration_number", "country"],
                field_weights={"registration_number": 0.8, "country": 0.2},
                threshold=0.95,
                auto_merge_threshold=1.0,
                auto_merge_enabled=True,
                is_active=True,
                priority=1,
                created_by="system"
            ),
        ]

        for rule in default_rules:
            self._resolution_rules[rule.rule_id] = rule

    async def create_master_entity(
        self, entity_type: EntityType, primary_name: str, source_record: SourceRecord
    ) -> MasterEntity:
        """Create a new master entity"""
        entity = MasterEntity(
            entity_type=entity_type,
            primary_name=primary_name,
            name_variants=source_record.names,
            addresses=source_record.addresses,
            identifiers=source_record.identifiers,
            date_of_birth=source_record.date_of_birth,
            source_record_ids=[source_record.record_id],
            source_systems=[source_record.source_system]
        )

        # Calculate quality scores
        entity.completeness_score = self._calculate_completeness(entity)
        entity.overall_quality_score = entity.completeness_score

        self._master_entities[entity.entity_id] = entity

        # Link source record
        source_record.master_entity_id = entity.entity_id
        source_record.resolution_status = ResolutionStatus.AUTO_RESOLVED
        source_record.resolved_at = datetime.utcnow()

        return entity

    async def get_master_entity(self, entity_id: UUID) -> Optional[MasterEntity]:
        """Get master entity by ID"""
        return self._master_entities.get(entity_id)

    async def ingest_source_record(self, record: SourceRecord) -> SourceRecord:
        """Ingest a new source record for resolution"""
        self._source_records[record.record_id] = record
        return record

    async def resolve_record(self, record_id: str) -> Tuple[Optional[MasterEntity], List[MatchCandidate]]:
        """Resolve a source record to master entity"""
        record = self._source_records.get(record_id)
        if not record:
            raise ValueError(f"Source record {record_id} not found")

        # Find potential matches
        candidates = await self._find_candidates(record)

        if not candidates:
            # No matches - create new master entity
            entity = await self.create_master_entity(
                record.entity_type,
                record.names[0].full_name if record.names else "Unknown",
                record
            )
            return entity, []

        # Check for auto-merge candidates
        best_candidate = max(candidates, key=lambda c: c.overall_score)

        if best_candidate.overall_score >= 0.98:
            # Auto-merge
            master_entity = self._master_entities.get(
                UUID(best_candidate.record_2_id) if best_candidate.record_2_source == "master"
                else None
            )
            if master_entity:
                await self._merge_record_to_entity(record, master_entity)
                return master_entity, candidates

        # Store candidates for review
        for candidate in candidates:
            self._match_candidates[candidate.candidate_id] = candidate

        return None, candidates

    async def _find_candidates(self, record: SourceRecord) -> List[MatchCandidate]:
        """Find potential matching entities"""
        candidates = []

        for entity in self._master_entities.values():
            if entity.entity_type != record.entity_type:
                continue

            candidate = await self._compare_to_entity(record, entity)
            if candidate and candidate.overall_score >= 0.5:
                candidates.append(candidate)

        return sorted(candidates, key=lambda c: c.overall_score, reverse=True)

    async def _compare_to_entity(
        self, record: SourceRecord, entity: MasterEntity
    ) -> Optional[MatchCandidate]:
        """Compare source record to master entity"""
        scores = {}
        matching_fields = []
        non_matching_fields = []

        # Name comparison
        if record.names and entity.name_variants:
            best_name_score = 0.0
            for rec_name in record.names:
                for ent_name in entity.name_variants:
                    score = self._compare_names(rec_name.full_name, ent_name.full_name)
                    best_name_score = max(best_name_score, score)

            scores["name"] = best_name_score
            if best_name_score >= 0.7:
                matching_fields.append("name")
            else:
                non_matching_fields.append("name")

        # DOB comparison
        if record.date_of_birth and entity.date_of_birth:
            if record.date_of_birth == entity.date_of_birth:
                scores["date_of_birth"] = 1.0
                matching_fields.append("date_of_birth")
            else:
                scores["date_of_birth"] = 0.0
                non_matching_fields.append("date_of_birth")

        # Identifier comparison
        identifier_score = 0.0
        for rec_id in record.identifiers:
            for ent_id in entity.identifiers:
                if (rec_id.identifier_type == ent_id.identifier_type and
                    rec_id.identifier_value == ent_id.identifier_value):
                    identifier_score = 1.0
                    matching_fields.append(f"identifier:{rec_id.identifier_type}")
                    break

        scores["identifier"] = identifier_score

        # Address comparison
        if record.addresses and entity.addresses:
            best_addr_score = 0.0
            for rec_addr in record.addresses:
                for ent_addr in entity.addresses:
                    score = self._compare_addresses(rec_addr, ent_addr)
                    best_addr_score = max(best_addr_score, score)

            scores["address"] = best_addr_score
            if best_addr_score >= 0.7:
                matching_fields.append("address")
            else:
                non_matching_fields.append("address")

        # Calculate overall score
        weights = {"name": 0.4, "date_of_birth": 0.2, "identifier": 0.25, "address": 0.15}
        overall_score = sum(
            scores.get(field, 0) * weight
            for field, weight in weights.items()
        )

        if overall_score < 0.5:
            return None

        confidence = MatchConfidence.DEFINITE if overall_score >= 0.95 else \
                    MatchConfidence.PROBABLE if overall_score >= 0.8 else \
                    MatchConfidence.POSSIBLE if overall_score >= 0.6 else \
                    MatchConfidence.UNLIKELY

        return MatchCandidate(
            record_1_id=record.record_id,
            record_1_source=record.source_system,
            record_2_id=str(entity.entity_id),
            record_2_source="master",
            overall_score=overall_score,
            confidence=confidence,
            name_score=scores.get("name", 0),
            address_score=scores.get("address", 0),
            identifier_score=scores.get("identifier", 0),
            dob_score=scores.get("date_of_birth", 0),
            matching_fields=matching_fields,
            non_matching_fields=non_matching_fields,
            score_breakdown=scores
        )

    def _compare_names(self, name1: str, name2: str) -> float:
        """Compare two names"""
        name1_norm = re.sub(r'[^a-z\s]', '', name1.lower())
        name2_norm = re.sub(r'[^a-z\s]', '', name2.lower())

        if name1_norm == name2_norm:
            return 1.0

        tokens1 = set(name1_norm.split())
        tokens2 = set(name2_norm.split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)

    def _compare_addresses(self, addr1: AddressRecord, addr2: AddressRecord) -> float:
        """Compare two addresses"""
        score = 0.0
        comparisons = 0

        if addr1.country == addr2.country:
            score += 1.0
            comparisons += 1

        if addr1.city and addr2.city:
            if addr1.city.lower() == addr2.city.lower():
                score += 1.0
            comparisons += 1

        if addr1.postal_code and addr2.postal_code:
            if addr1.postal_code == addr2.postal_code:
                score += 1.0
            comparisons += 1

        if addr1.address_line1 and addr2.address_line1:
            addr_score = self._compare_names(addr1.address_line1, addr2.address_line1)
            score += addr_score
            comparisons += 1

        return score / comparisons if comparisons > 0 else 0.0

    async def _merge_record_to_entity(self, record: SourceRecord, entity: MasterEntity):
        """Merge source record into master entity"""
        # Add source record reference
        if record.record_id not in entity.source_record_ids:
            entity.source_record_ids.append(record.record_id)

        if record.source_system not in entity.source_systems:
            entity.source_systems.append(record.source_system)

        # Add name variants
        for name in record.names:
            if not any(n.full_name == name.full_name for n in entity.name_variants):
                entity.name_variants.append(name)

        # Add addresses
        for addr in record.addresses:
            if not any(a.address_line1 == addr.address_line1 and a.city == addr.city
                      for a in entity.addresses):
                entity.addresses.append(addr)

        # Add identifiers
        for identifier in record.identifiers:
            if not any(i.identifier_type == identifier.identifier_type and
                      i.identifier_value == identifier.identifier_value
                      for i in entity.identifiers):
                entity.identifiers.append(identifier)

        # Update record status
        record.master_entity_id = entity.entity_id
        record.resolution_status = ResolutionStatus.AUTO_RESOLVED
        record.resolution_confidence = 1.0
        record.resolved_at = datetime.utcnow()

        # Update entity
        entity.updated_at = datetime.utcnow()
        entity.last_resolved_at = datetime.utcnow()
        entity.completeness_score = self._calculate_completeness(entity)
        entity.overall_quality_score = entity.completeness_score

    async def merge_entities(
        self, entity_ids: List[UUID], surviving_entity_id: UUID, merged_by: str
    ) -> MergeOperation:
        """Merge multiple entities into one"""
        surviving = self._master_entities.get(surviving_entity_id)
        if not surviving:
            raise ValueError(f"Surviving entity {surviving_entity_id} not found")

        merge_op = MergeOperation(
            merge_type="manual",
            surviving_entity_id=surviving_entity_id,
            merged_entity_ids=[e for e in entity_ids if e != surviving_entity_id],
            merge_confidence=1.0,
            performed_by=merged_by
        )

        for entity_id in entity_ids:
            if entity_id == surviving_entity_id:
                continue

            entity = self._master_entities.get(entity_id)
            if not entity:
                continue

            # Merge data
            surviving.name_variants.extend(entity.name_variants)
            surviving.addresses.extend(entity.addresses)
            surviving.identifiers.extend(entity.identifiers)
            surviving.relationships.extend(entity.relationships)
            surviving.source_record_ids.extend(entity.source_record_ids)
            surviving.source_systems.extend(
                [s for s in entity.source_systems if s not in surviving.source_systems]
            )

            # Update source records
            for record_id in entity.source_record_ids:
                record = self._source_records.get(record_id)
                if record:
                    record.master_entity_id = surviving_entity_id

            # Add to merge history
            surviving.merge_history.append({
                "merged_entity_id": str(entity_id),
                "merged_at": datetime.utcnow().isoformat(),
                "merged_by": merged_by
            })

            # Remove merged entity
            del self._master_entities[entity_id]

        surviving.updated_at = datetime.utcnow()
        surviving.last_resolved_at = datetime.utcnow()

        self._merge_operations[merge_op.merge_id] = merge_op
        return merge_op

    async def split_entity(
        self, entity_id: UUID, record_assignments: Dict[str, str], split_by: str, reason: str
    ) -> SplitOperation:
        """Split a master entity into multiple entities"""
        entity = self._master_entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        split_op = SplitOperation(
            original_entity_id=entity_id,
            split_reason=reason,
            record_assignments=record_assignments,
            performed_by=split_by
        )

        # Group records by new entity
        new_entity_groups: Dict[str, List[str]] = defaultdict(list)
        for record_id, new_entity_name in record_assignments.items():
            new_entity_groups[new_entity_name].append(record_id)

        # Create new entities
        for new_entity_name, record_ids in new_entity_groups.items():
            if not record_ids:
                continue

            # Get first record to establish entity
            first_record = self._source_records.get(record_ids[0])
            if not first_record:
                continue

            new_entity = await self.create_master_entity(
                entity.entity_type,
                new_entity_name,
                first_record
            )

            # Add remaining records
            for record_id in record_ids[1:]:
                record = self._source_records.get(record_id)
                if record:
                    await self._merge_record_to_entity(record, new_entity)

            split_op.new_entity_ids.append(new_entity.entity_id)

        # Remove original entity
        del self._master_entities[entity_id]

        return split_op

    async def review_candidate(
        self, candidate_id: UUID, decision: str, reviewed_by: str, notes: Optional[str] = None
    ) -> Optional[MatchCandidate]:
        """Review a match candidate"""
        candidate = self._match_candidates.get(candidate_id)
        if not candidate:
            return None

        candidate.status = decision
        candidate.resolved_by = reviewed_by
        candidate.resolved_at = datetime.utcnow()
        candidate.resolution_notes = notes

        if decision == "confirmed":
            # Merge the records
            record = self._source_records.get(candidate.record_1_id)
            entity = self._master_entities.get(UUID(candidate.record_2_id))

            if record and entity:
                await self._merge_record_to_entity(record, entity)
                record.resolution_status = ResolutionStatus.MANUALLY_RESOLVED

        elif decision == "rejected":
            # Create new master entity
            record = self._source_records.get(candidate.record_1_id)
            if record:
                await self.create_master_entity(
                    record.entity_type,
                    record.names[0].full_name if record.names else "Unknown",
                    record
                )

        return candidate

    def _calculate_completeness(self, entity: MasterEntity) -> float:
        """Calculate data completeness score"""
        score = 0.0
        fields = 0

        if entity.primary_name:
            score += 1.0
            fields += 1

        if entity.date_of_birth:
            score += 1.0
            fields += 1

        if entity.identifiers:
            score += 1.0
            fields += 1

        if entity.addresses:
            score += 1.0
            fields += 1

        if entity.nationalities:
            score += 0.5
            fields += 0.5

        return (score / fields * 100) if fields > 0 else 0.0

    async def get_statistics(self) -> EntityResolutionStatistics:
        """Get entity resolution statistics"""
        stats = EntityResolutionStatistics()
        stats.total_master_entities = len(self._master_entities)
        stats.total_source_records = len(self._source_records)

        # Unresolved records
        stats.unresolved_records = len([
            r for r in self._source_records.values()
            if r.resolution_status == ResolutionStatus.PENDING
        ])

        # Pending review
        stats.pending_review = len([
            c for c in self._match_candidates.values()
            if c.status == "pending"
        ])

        # By entity type
        for entity in self._master_entities.values():
            type_key = entity.entity_type.value
            stats.by_entity_type[type_key] = stats.by_entity_type.get(type_key, 0) + 1

        # By source system
        for record in self._source_records.values():
            system = record.source_system
            stats.by_source_system[system] = stats.by_source_system.get(system, 0) + 1

        # Merge/split counts
        stats.merges_this_month = len(self._merge_operations)

        # Data quality
        if self._master_entities:
            stats.data_quality_score = sum(
                e.overall_quality_score for e in self._master_entities.values()
            ) / len(self._master_entities)

        return stats


# Global service instance
entity_resolution_service = EntityResolutionService()
