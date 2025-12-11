"""Master Data Management Repository"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.master_data_models import (
    MasterDataDomain, MasterEntity, MatchRule, MergeRule, MatchCandidate,
    MergeHistory, DataStewardshipTask, GoldenRecordAudit
)


class MasterDataRepository:
    def __init__(self):
        self._domains: Dict[UUID, MasterDataDomain] = {}
        self._entities: Dict[UUID, MasterEntity] = {}
        self._match_rules: Dict[UUID, MatchRule] = {}
        self._merge_rules: Dict[UUID, MergeRule] = {}
        self._match_candidates: Dict[UUID, MatchCandidate] = {}
        self._merge_histories: Dict[UUID, MergeHistory] = {}
        self._tasks: Dict[UUID, DataStewardshipTask] = {}
        self._audits: Dict[UUID, GoldenRecordAudit] = {}

    async def save_domain(self, domain: MasterDataDomain) -> MasterDataDomain:
        self._domains[domain.domain_id] = domain
        return domain

    async def find_domain_by_id(self, domain_id: UUID) -> Optional[MasterDataDomain]:
        return self._domains.get(domain_id)

    async def find_all_domains(self) -> List[MasterDataDomain]:
        return list(self._domains.values())

    async def find_domain_by_code(self, domain_code: str) -> Optional[MasterDataDomain]:
        for domain in self._domains.values():
            if domain.domain_code == domain_code:
                return domain
        return None

    async def delete_domain(self, domain_id: UUID) -> bool:
        if domain_id in self._domains:
            del self._domains[domain_id]
            return True
        return False

    async def save_entity(self, entity: MasterEntity) -> MasterEntity:
        self._entities[entity.entity_id] = entity
        return entity

    async def find_entity_by_id(self, entity_id: UUID) -> Optional[MasterEntity]:
        return self._entities.get(entity_id)

    async def find_all_entities(self) -> List[MasterEntity]:
        return list(self._entities.values())

    async def find_entities_by_domain(self, domain_id: UUID) -> List[MasterEntity]:
        return [e for e in self._entities.values() if e.domain_id == domain_id]

    async def find_entities_by_type(self, entity_type: str) -> List[MasterEntity]:
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    async def find_entity_by_golden_record_id(self, golden_record_id: str) -> Optional[MasterEntity]:
        for entity in self._entities.values():
            if entity.golden_record_id == golden_record_id:
                return entity
        return None

    async def delete_entity(self, entity_id: UUID) -> bool:
        if entity_id in self._entities:
            del self._entities[entity_id]
            return True
        return False

    async def save_match_rule(self, rule: MatchRule) -> MatchRule:
        self._match_rules[rule.rule_id] = rule
        return rule

    async def find_match_rule_by_id(self, rule_id: UUID) -> Optional[MatchRule]:
        return self._match_rules.get(rule_id)

    async def find_all_match_rules(self) -> List[MatchRule]:
        return list(self._match_rules.values())

    async def find_match_rules_by_domain(self, domain_id: UUID) -> List[MatchRule]:
        return [r for r in self._match_rules.values() if r.domain_id == domain_id]

    async def find_active_match_rules(self) -> List[MatchRule]:
        return [r for r in self._match_rules.values() if r.is_active]

    async def save_merge_rule(self, rule: MergeRule) -> MergeRule:
        self._merge_rules[rule.rule_id] = rule
        return rule

    async def find_merge_rule_by_id(self, rule_id: UUID) -> Optional[MergeRule]:
        return self._merge_rules.get(rule_id)

    async def find_all_merge_rules(self) -> List[MergeRule]:
        return list(self._merge_rules.values())

    async def find_merge_rules_by_domain(self, domain_id: UUID) -> List[MergeRule]:
        return [r for r in self._merge_rules.values() if r.domain_id == domain_id]

    async def save_match_candidate(self, candidate: MatchCandidate) -> MatchCandidate:
        self._match_candidates[candidate.candidate_id] = candidate
        return candidate

    async def find_match_candidate_by_id(self, candidate_id: UUID) -> Optional[MatchCandidate]:
        return self._match_candidates.get(candidate_id)

    async def find_all_match_candidates(self) -> List[MatchCandidate]:
        return list(self._match_candidates.values())

    async def find_pending_match_candidates(self) -> List[MatchCandidate]:
        return [c for c in self._match_candidates.values() if c.match_status == "pending_review"]

    async def find_match_candidates_by_domain(self, domain_id: UUID) -> List[MatchCandidate]:
        return [c for c in self._match_candidates.values() if c.domain_id == domain_id]

    async def save_merge_history(self, merge: MergeHistory) -> MergeHistory:
        self._merge_histories[merge.merge_id] = merge
        return merge

    async def find_merge_history_by_id(self, merge_id: UUID) -> Optional[MergeHistory]:
        return self._merge_histories.get(merge_id)

    async def find_all_merge_histories(self) -> List[MergeHistory]:
        return list(self._merge_histories.values())

    async def find_merge_histories_by_entity(self, entity_id: UUID) -> List[MergeHistory]:
        return [m for m in self._merge_histories.values() if m.entity_id == entity_id]

    async def save_task(self, task: DataStewardshipTask) -> DataStewardshipTask:
        self._tasks[task.task_id] = task
        return task

    async def find_task_by_id(self, task_id: UUID) -> Optional[DataStewardshipTask]:
        return self._tasks.get(task_id)

    async def find_all_tasks(self) -> List[DataStewardshipTask]:
        return list(self._tasks.values())

    async def find_tasks_by_assignee(self, assigned_to: str) -> List[DataStewardshipTask]:
        return [t for t in self._tasks.values() if t.assigned_to == assigned_to]

    async def find_pending_tasks(self) -> List[DataStewardshipTask]:
        return [t for t in self._tasks.values() if t.status == "pending"]

    async def find_tasks_by_domain(self, domain_id: UUID) -> List[DataStewardshipTask]:
        return [t for t in self._tasks.values() if t.domain_id == domain_id]

    async def save_audit(self, audit: GoldenRecordAudit) -> GoldenRecordAudit:
        self._audits[audit.audit_id] = audit
        return audit

    async def find_audit_by_id(self, audit_id: UUID) -> Optional[GoldenRecordAudit]:
        return self._audits.get(audit_id)

    async def find_all_audits(self) -> List[GoldenRecordAudit]:
        return list(self._audits.values())

    async def find_audits_by_entity(self, entity_id: UUID) -> List[GoldenRecordAudit]:
        return [a for a in self._audits.values() if a.entity_id == entity_id]

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_domains": len(self._domains),
            "total_entities": len(self._entities),
            "active_entities": len([e for e in self._entities.values() if e.status.value == "active"]),
            "total_match_rules": len(self._match_rules),
            "total_merge_rules": len(self._merge_rules),
            "pending_match_candidates": len([c for c in self._match_candidates.values() if c.match_status == "pending_review"]),
            "total_merge_histories": len(self._merge_histories),
            "pending_tasks": len([t for t in self._tasks.values() if t.status == "pending"]),
            "total_audits": len(self._audits),
        }


master_data_repository = MasterDataRepository()
