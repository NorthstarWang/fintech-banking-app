"""Master Data Management Service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.master_data_models import (
    MasterDataDomain, MasterEntity, MatchRule, MergeRule, MatchCandidate,
    MergeHistory, DataStewardshipTask, GoldenRecordAudit, EntityStatus
)
from ..repositories.master_data_repository import master_data_repository


class MasterDataService:
    def __init__(self):
        self.repository = master_data_repository
        self._entity_counter = 0
        self._task_counter = 0

    async def create_domain(
        self, domain_name: str, domain_code: str, description: str,
        owner: str, steward: str, source_systems: List[str], entity_types: List[str]
    ) -> MasterDataDomain:
        domain = MasterDataDomain(
            domain_name=domain_name, domain_code=domain_code, description=description,
            owner=owner, steward=steward, source_systems=source_systems,
            entity_types=entity_types
        )
        await self.repository.save_domain(domain)
        return domain

    async def create_master_entity(
        self, domain_id: UUID, entity_type: str, entity_name: str,
        attributes: Dict[str, Any], source_records: List[Dict[str, Any]],
        created_by: str
    ) -> MasterEntity:
        self._entity_counter += 1
        entity = MasterEntity(
            domain_id=domain_id, entity_type=entity_type,
            golden_record_id=f"GR-{entity_type[:3].upper()}-{self._entity_counter:08d}",
            entity_name=entity_name, attributes=attributes,
            source_records=source_records, created_by=created_by, updated_by=created_by
        )
        await self.repository.save_entity(entity)
        return entity

    async def create_match_rule(
        self, domain_id: UUID, rule_name: str, rule_description: str,
        match_type: str, match_fields: List[str], match_threshold: Decimal,
        created_by: str, is_blocking_rule: bool = False
    ) -> MatchRule:
        rule = MatchRule(
            domain_id=domain_id, rule_name=rule_name, rule_description=rule_description,
            match_type=match_type, match_fields=match_fields,
            match_threshold=match_threshold, is_blocking_rule=is_blocking_rule,
            created_by=created_by
        )
        await self.repository.save_match_rule(rule)
        return rule

    async def create_merge_rule(
        self, domain_id: UUID, rule_name: str, attribute_name: str,
        survivorship_rule: str, source_priority: List[str] = None
    ) -> MergeRule:
        rule = MergeRule(
            domain_id=domain_id, rule_name=rule_name, attribute_name=attribute_name,
            survivorship_rule=survivorship_rule, source_priority=source_priority or []
        )
        await self.repository.save_merge_rule(rule)
        return rule

    async def create_match_candidate(
        self, domain_id: UUID, entity_type: str, record_1_id: str, record_1_source: str,
        record_2_id: str, record_2_source: str, match_score: Decimal,
        matched_fields: Dict[str, Decimal]
    ) -> MatchCandidate:
        candidate = MatchCandidate(
            domain_id=domain_id, entity_type=entity_type,
            record_1_id=record_1_id, record_1_source=record_1_source,
            record_2_id=record_2_id, record_2_source=record_2_source,
            match_score=match_score, matched_fields=matched_fields
        )
        await self.repository.save_match_candidate(candidate)
        return candidate

    async def confirm_match(self, candidate_id: UUID, reviewed_by: str) -> Optional[MatchCandidate]:
        candidate = await self.repository.find_match_candidate_by_id(candidate_id)
        if candidate:
            candidate.match_status = "confirmed"
            candidate.reviewed_by = reviewed_by
            candidate.review_date = datetime.utcnow()
        return candidate

    async def merge_entities(
        self, entity_id: UUID, merged_records: List[str], merged_by: str,
        survivorship_decisions: Dict[str, str]
    ) -> MergeHistory:
        merge = MergeHistory(
            entity_id=entity_id, merged_records=merged_records,
            merge_type="manual", merged_by=merged_by,
            survivorship_decisions=survivorship_decisions
        )
        await self.repository.save_merge_history(merge)
        return merge

    async def create_stewardship_task(
        self, domain_id: UUID, task_type: str, description: str,
        entity_ids: List[UUID], assigned_to: str, due_date: date, priority: str = "normal"
    ) -> DataStewardshipTask:
        self._task_counter += 1
        task = DataStewardshipTask(
            domain_id=domain_id, task_type=task_type, description=description,
            entity_ids=entity_ids, priority=priority, assigned_to=assigned_to,
            assigned_date=datetime.utcnow(), due_date=due_date
        )
        await self.repository.save_task(task)
        return task

    async def complete_task(
        self, task_id: UUID, resolution: str
    ) -> Optional[DataStewardshipTask]:
        task = await self.repository.find_task_by_id(task_id)
        if task:
            task.status = "completed"
            task.resolution = resolution
            task.completed_date = datetime.utcnow()
        return task

    async def audit_entity_change(
        self, entity_id: UUID, action: str, performed_by: str,
        previous_state: Dict[str, Any], new_state: Dict[str, Any], reason: str = ""
    ) -> GoldenRecordAudit:
        audit = GoldenRecordAudit(
            entity_id=entity_id, action=action, performed_by=performed_by,
            previous_state=previous_state, new_state=new_state, reason=reason
        )
        await self.repository.save_audit(audit)
        return audit

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


master_data_service = MasterDataService()
