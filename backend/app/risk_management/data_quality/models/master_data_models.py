"""Master Data Management Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class EntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    MERGED = "merged"
    DELETED = "deleted"


class MasterDataDomain(BaseModel):
    domain_id: UUID = Field(default_factory=uuid4)
    domain_name: str
    domain_code: str
    description: str
    owner: str
    steward: str
    source_systems: List[str] = Field(default_factory=list)
    entity_types: List[str] = Field(default_factory=list)
    governance_policy: str = ""
    created_date: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class MasterEntity(BaseModel):
    entity_id: UUID = Field(default_factory=uuid4)
    domain_id: UUID
    entity_type: str
    golden_record_id: str
    entity_name: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_records: List[Dict[str, Any]] = Field(default_factory=list)
    match_confidence: Decimal = Decimal("100")
    status: EntityStatus = EntityStatus.ACTIVE
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""
    updated_by: str = ""


class MatchRule(BaseModel):
    rule_id: UUID = Field(default_factory=uuid4)
    domain_id: UUID
    rule_name: str
    rule_description: str
    match_type: str  # exact, fuzzy, probabilistic
    match_fields: List[str] = Field(default_factory=list)
    match_threshold: Decimal = Decimal("80")
    weight: Decimal = Decimal("1")
    is_blocking_rule: bool = False
    blocking_keys: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_by: str = ""


class MergeRule(BaseModel):
    rule_id: UUID = Field(default_factory=uuid4)
    domain_id: UUID
    rule_name: str
    attribute_name: str
    survivorship_rule: str  # most_recent, most_complete, source_priority, aggregate
    source_priority: List[str] = Field(default_factory=list)
    is_active: bool = True


class MatchCandidate(BaseModel):
    candidate_id: UUID = Field(default_factory=uuid4)
    domain_id: UUID
    entity_type: str
    record_1_id: str
    record_1_source: str
    record_2_id: str
    record_2_source: str
    match_score: Decimal
    matched_fields: Dict[str, Decimal] = Field(default_factory=dict)
    match_status: str = "pending"  # pending, confirmed, rejected, auto_merged
    reviewed_by: Optional[str] = None
    review_date: Optional[datetime] = None
    created_date: datetime = Field(default_factory=datetime.utcnow)


class MergeHistory(BaseModel):
    merge_id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    merged_records: List[str] = Field(default_factory=list)
    merge_date: datetime = Field(default_factory=datetime.utcnow)
    merge_type: str  # auto, manual
    merged_by: str = ""
    survivorship_decisions: Dict[str, str] = Field(default_factory=dict)
    can_unmerge: bool = True


class DataStewardshipTask(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    domain_id: UUID
    task_type: str  # match_review, merge_approval, data_correction, exception_handling
    description: str
    entity_ids: List[UUID] = Field(default_factory=list)
    priority: str = "normal"
    assigned_to: str = ""
    assigned_date: Optional[datetime] = None
    due_date: Optional[date] = None
    status: str = "pending"
    resolution: str = ""
    completed_date: Optional[datetime] = None
    created_date: datetime = Field(default_factory=datetime.utcnow)


class GoldenRecordAudit(BaseModel):
    audit_id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    action: str  # create, update, merge, unmerge, delete
    action_date: datetime = Field(default_factory=datetime.utcnow)
    performed_by: str
    previous_state: Dict[str, Any] = Field(default_factory=dict)
    new_state: Dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
