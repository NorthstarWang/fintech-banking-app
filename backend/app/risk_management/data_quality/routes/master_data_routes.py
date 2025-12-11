"""Master Data Management Routes"""

from typing import List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.master_data_service import master_data_service

router = APIRouter(prefix="/master-data", tags=["Master Data Management"])


class CreateDomainRequest(BaseModel):
    domain_name: str
    domain_code: str
    description: str
    owner: str
    steward: str
    source_systems: List[str]
    entity_types: List[str]


class CreateEntityRequest(BaseModel):
    domain_id: UUID
    entity_type: str
    entity_name: str
    attributes: Dict[str, Any]
    source_records: List[Dict[str, Any]]
    created_by: str


class CreateMatchRuleRequest(BaseModel):
    domain_id: UUID
    rule_name: str
    rule_description: str
    match_type: str
    match_fields: List[str]
    match_threshold: Decimal
    created_by: str
    is_blocking_rule: bool = False


class CreateMergeRuleRequest(BaseModel):
    domain_id: UUID
    rule_name: str
    attribute_name: str
    survivorship_rule: str
    source_priority: List[str] = []


class CreateMatchCandidateRequest(BaseModel):
    domain_id: UUID
    entity_type: str
    record_1_id: str
    record_1_source: str
    record_2_id: str
    record_2_source: str
    match_score: Decimal
    matched_fields: Dict[str, Decimal]


class MergeEntitiesRequest(BaseModel):
    entity_id: UUID
    merged_records: List[str]
    merged_by: str
    survivorship_decisions: Dict[str, str]


class CreateTaskRequest(BaseModel):
    domain_id: UUID
    task_type: str
    description: str
    entity_ids: List[UUID]
    assigned_to: str
    due_date: date
    priority: str = "normal"


class AuditEntityRequest(BaseModel):
    entity_id: UUID
    action: str
    performed_by: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    reason: str = ""


@router.post("/domains")
async def create_domain(request: CreateDomainRequest):
    domain = await master_data_service.create_domain(
        domain_name=request.domain_name,
        domain_code=request.domain_code,
        description=request.description,
        owner=request.owner,
        steward=request.steward,
        source_systems=request.source_systems,
        entity_types=request.entity_types,
    )
    return {"status": "created", "domain_id": str(domain.domain_id)}


@router.get("/domains")
async def get_all_domains():
    domains = await master_data_service.repository.find_all_domains()
    return {"domains": [{"domain_id": str(d.domain_id), "name": d.domain_name, "code": d.domain_code} for d in domains]}


@router.get("/domains/{domain_id}")
async def get_domain(domain_id: UUID):
    domain = await master_data_service.repository.find_domain_by_id(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.post("/entities")
async def create_entity(request: CreateEntityRequest):
    entity = await master_data_service.create_master_entity(
        domain_id=request.domain_id,
        entity_type=request.entity_type,
        entity_name=request.entity_name,
        attributes=request.attributes,
        source_records=request.source_records,
        created_by=request.created_by,
    )
    return {"status": "created", "entity_id": str(entity.entity_id), "golden_record_id": entity.golden_record_id}


@router.get("/entities")
async def get_all_entities():
    entities = await master_data_service.repository.find_all_entities()
    return {"entities": [{"entity_id": str(e.entity_id), "name": e.entity_name, "golden_id": e.golden_record_id} for e in entities]}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: UUID):
    entity = await master_data_service.repository.find_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/entities/golden/{golden_record_id}")
async def get_entity_by_golden_id(golden_record_id: str):
    entity = await master_data_service.repository.find_entity_by_golden_record_id(golden_record_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.post("/match-rules")
async def create_match_rule(request: CreateMatchRuleRequest):
    rule = await master_data_service.create_match_rule(
        domain_id=request.domain_id,
        rule_name=request.rule_name,
        rule_description=request.rule_description,
        match_type=request.match_type,
        match_fields=request.match_fields,
        match_threshold=request.match_threshold,
        created_by=request.created_by,
        is_blocking_rule=request.is_blocking_rule,
    )
    return {"status": "created", "rule_id": str(rule.rule_id)}


@router.get("/match-rules")
async def get_all_match_rules():
    rules = await master_data_service.repository.find_all_match_rules()
    return {"rules": [{"rule_id": str(r.rule_id), "name": r.rule_name, "type": r.match_type} for r in rules]}


@router.post("/merge-rules")
async def create_merge_rule(request: CreateMergeRuleRequest):
    rule = await master_data_service.create_merge_rule(
        domain_id=request.domain_id,
        rule_name=request.rule_name,
        attribute_name=request.attribute_name,
        survivorship_rule=request.survivorship_rule,
        source_priority=request.source_priority,
    )
    return {"status": "created", "rule_id": str(rule.rule_id)}


@router.get("/merge-rules")
async def get_all_merge_rules():
    rules = await master_data_service.repository.find_all_merge_rules()
    return {"rules": [{"rule_id": str(r.rule_id), "name": r.rule_name, "attribute": r.attribute_name} for r in rules]}


@router.post("/match-candidates")
async def create_match_candidate(request: CreateMatchCandidateRequest):
    candidate = await master_data_service.create_match_candidate(
        domain_id=request.domain_id,
        entity_type=request.entity_type,
        record_1_id=request.record_1_id,
        record_1_source=request.record_1_source,
        record_2_id=request.record_2_id,
        record_2_source=request.record_2_source,
        match_score=request.match_score,
        matched_fields=request.matched_fields,
    )
    return {"status": "created", "candidate_id": str(candidate.candidate_id)}


@router.post("/match-candidates/{candidate_id}/confirm")
async def confirm_match(candidate_id: UUID, reviewed_by: str):
    candidate = await master_data_service.confirm_match(
        candidate_id=candidate_id,
        reviewed_by=reviewed_by,
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"status": "confirmed", "candidate_id": str(candidate.candidate_id)}


@router.get("/match-candidates")
async def get_all_match_candidates():
    candidates = await master_data_service.repository.find_all_match_candidates()
    return {"candidates": [{"id": str(c.candidate_id), "score": float(c.match_score), "status": c.match_status} for c in candidates]}


@router.get("/match-candidates/pending")
async def get_pending_match_candidates():
    candidates = await master_data_service.repository.find_pending_match_candidates()
    return {"candidates": [{"id": str(c.candidate_id), "score": float(c.match_score)} for c in candidates]}


@router.post("/merges")
async def merge_entities(request: MergeEntitiesRequest):
    merge = await master_data_service.merge_entities(
        entity_id=request.entity_id,
        merged_records=request.merged_records,
        merged_by=request.merged_by,
        survivorship_decisions=request.survivorship_decisions,
    )
    return {"status": "merged", "merge_id": str(merge.merge_id)}


@router.get("/merges")
async def get_all_merge_histories():
    merges = await master_data_service.repository.find_all_merge_histories()
    return {"merges": [{"merge_id": str(m.merge_id), "entity_id": str(m.entity_id), "type": m.merge_type} for m in merges]}


@router.post("/tasks")
async def create_task(request: CreateTaskRequest):
    task = await master_data_service.create_stewardship_task(
        domain_id=request.domain_id,
        task_type=request.task_type,
        description=request.description,
        entity_ids=request.entity_ids,
        assigned_to=request.assigned_to,
        due_date=request.due_date,
        priority=request.priority,
    )
    return {"status": "created", "task_id": str(task.task_id)}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: UUID, resolution: str):
    task = await master_data_service.complete_task(
        task_id=task_id,
        resolution=resolution,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "completed", "task_id": str(task.task_id)}


@router.get("/tasks")
async def get_all_tasks():
    tasks = await master_data_service.repository.find_all_tasks()
    return {"tasks": [{"task_id": str(t.task_id), "type": t.task_type, "status": t.status} for t in tasks]}


@router.get("/tasks/pending")
async def get_pending_tasks():
    tasks = await master_data_service.repository.find_pending_tasks()
    return {"tasks": [{"task_id": str(t.task_id), "type": t.task_type, "assigned_to": t.assigned_to} for t in tasks]}


@router.post("/audits")
async def audit_entity_change(request: AuditEntityRequest):
    audit = await master_data_service.audit_entity_change(
        entity_id=request.entity_id,
        action=request.action,
        performed_by=request.performed_by,
        previous_state=request.previous_state,
        new_state=request.new_state,
        reason=request.reason,
    )
    return {"status": "recorded", "audit_id": str(audit.audit_id)}


@router.get("/audits")
async def get_all_audits():
    audits = await master_data_service.repository.find_all_audits()
    return {"audits": [{"audit_id": str(a.audit_id), "entity_id": str(a.entity_id), "action": a.action} for a in audits]}


@router.get("/audits/entity/{entity_id}")
async def get_entity_audits(entity_id: UUID):
    audits = await master_data_service.repository.find_audits_by_entity(entity_id)
    return {"audits": [{"audit_id": str(a.audit_id), "action": a.action, "performed_by": a.performed_by} for a in audits]}


@router.get("/statistics")
async def get_statistics():
    return await master_data_service.get_statistics()
