"""
Entity Resolution Models

Defines data structures for entity resolution and identity matching.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class EntityType(str, Enum):
    """Types of entities"""
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"
    ACCOUNT = "account"
    TRANSACTION = "transaction"


class MatchConfidence(str, Enum):
    """Confidence level of a match"""
    DEFINITE = "definite"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"


class ResolutionStatus(str, Enum):
    """Status of entity resolution"""
    PENDING = "pending"
    AUTO_RESOLVED = "auto_resolved"
    MANUALLY_RESOLVED = "manually_resolved"
    REJECTED = "rejected"
    SPLIT = "split"


class IdentityAttribute(BaseModel):
    """Individual identity attribute"""
    attribute_id: UUID = Field(default_factory=uuid4)
    attribute_type: str
    attribute_value: str
    confidence: float = 1.0
    source_system: str
    source_record_id: str
    captured_at: datetime
    is_primary: bool = False
    is_verified: bool = False


class NameVariant(BaseModel):
    """Name variant for an entity"""
    variant_id: UUID = Field(default_factory=uuid4)
    name_type: str  # legal, maiden, alias, trading_name, former
    full_name: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    prefix: Optional[str] = None
    source_system: str
    confidence: float = 1.0
    is_primary: bool = False


class AddressRecord(BaseModel):
    """Address record for an entity"""
    address_id: UUID = Field(default_factory=uuid4)
    address_type: str  # residential, business, mailing, registered
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    is_current: bool = True
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source_system: str
    confidence: float = 1.0


class IdentifierRecord(BaseModel):
    """Identifier record for an entity"""
    identifier_id: UUID = Field(default_factory=uuid4)
    identifier_type: str  # ssn, ein, passport, account, phone, email
    identifier_value: str
    issuing_authority: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_verified: bool = False
    source_system: str
    confidence: float = 1.0


class RelationshipRecord(BaseModel):
    """Relationship between entities"""
    relationship_id: UUID = Field(default_factory=uuid4)
    related_entity_id: UUID
    relationship_type: str  # spouse, child, parent, employer, employee, owner, director
    relationship_role: str  # from perspective of the primary entity
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    ownership_percentage: Optional[float] = None
    source_system: str
    confidence: float = 1.0


class MasterEntity(BaseModel):
    """Master entity record (golden record)"""
    entity_id: UUID = Field(default_factory=uuid4)
    entity_type: EntityType

    # Resolved name
    primary_name: str
    name_variants: List[NameVariant] = Field(default_factory=list)

    # Demographics (for individuals)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationalities: List[str] = Field(default_factory=list)

    # Organization details
    incorporation_date: Optional[date] = None
    incorporation_country: Optional[str] = None
    business_type: Optional[str] = None

    # Addresses
    addresses: List[AddressRecord] = Field(default_factory=list)
    primary_address: Optional[AddressRecord] = None

    # Identifiers
    identifiers: List[IdentifierRecord] = Field(default_factory=list)

    # Relationships
    relationships: List[RelationshipRecord] = Field(default_factory=list)

    # Source records
    source_record_ids: List[str] = Field(default_factory=list)
    source_systems: List[str] = Field(default_factory=list)

    # Data quality
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    timeliness_score: float = 0.0
    consistency_score: float = 0.0
    overall_quality_score: float = 0.0

    # Risk attributes
    risk_score: float = 0.0
    risk_flags: List[str] = Field(default_factory=list)
    is_pep: bool = False
    is_sanctioned: bool = False
    is_on_watchlist: bool = False

    # Status
    status: str = "active"
    merge_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_resolved_at: Optional[datetime] = None


class SourceRecord(BaseModel):
    """Source record from a system"""
    record_id: str
    source_system: str
    entity_type: EntityType

    # Raw data
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    # Extracted attributes
    names: List[NameVariant] = Field(default_factory=list)
    addresses: List[AddressRecord] = Field(default_factory=list)
    identifiers: List[IdentifierRecord] = Field(default_factory=list)
    date_of_birth: Optional[date] = None
    additional_attributes: Dict[str, Any] = Field(default_factory=dict)

    # Resolution status
    master_entity_id: Optional[UUID] = None
    resolution_status: ResolutionStatus = ResolutionStatus.PENDING
    resolution_confidence: float = 0.0

    # Timestamps
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class MatchCandidate(BaseModel):
    """Candidate match between records"""
    candidate_id: UUID = Field(default_factory=uuid4)

    # Records being compared
    record_1_id: str
    record_1_source: str
    record_2_id: str
    record_2_source: str

    # Match scores
    overall_score: float
    confidence: MatchConfidence

    # Field-level scores
    name_score: float = 0.0
    address_score: float = 0.0
    identifier_score: float = 0.0
    dob_score: float = 0.0

    # Matching details
    matching_fields: List[str] = Field(default_factory=list)
    non_matching_fields: List[str] = Field(default_factory=list)
    score_breakdown: Dict[str, float] = Field(default_factory=dict)

    # Status
    status: str = "pending"  # pending, confirmed, rejected
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    # Timestamps
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class MergeOperation(BaseModel):
    """Record of a merge operation"""
    merge_id: UUID = Field(default_factory=uuid4)

    # Merge type
    merge_type: str  # auto, manual

    # Entities involved
    surviving_entity_id: UUID
    merged_entity_ids: List[UUID] = Field(default_factory=list)

    # Match information
    match_candidate_ids: List[UUID] = Field(default_factory=list)
    merge_confidence: float

    # Before/After
    pre_merge_state: Dict[str, Any] = Field(default_factory=dict)
    post_merge_state: Dict[str, Any] = Field(default_factory=dict)

    # Conflicts resolved
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    conflict_resolutions: List[Dict[str, Any]] = Field(default_factory=list)

    # Performed by
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Rollback
    can_rollback: bool = True
    rolled_back: bool = False
    rollback_at: Optional[datetime] = None


class SplitOperation(BaseModel):
    """Record of a split operation"""
    split_id: UUID = Field(default_factory=uuid4)

    # Original entity
    original_entity_id: UUID

    # New entities
    new_entity_ids: List[UUID] = Field(default_factory=list)

    # Split details
    split_reason: str
    record_assignments: Dict[str, str] = Field(default_factory=dict)  # record_id -> new_entity_id

    # Performed by
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class ResolutionRule(BaseModel):
    """Rule for automatic entity resolution"""
    rule_id: UUID = Field(default_factory=uuid4)
    rule_name: str
    rule_code: str

    # Rule configuration
    entity_type: EntityType
    match_fields: List[str] = Field(default_factory=list)
    field_weights: Dict[str, float] = Field(default_factory=dict)
    threshold: float = 0.85

    # Auto-merge settings
    auto_merge_threshold: float = 0.95
    auto_merge_enabled: bool = True

    # Status
    is_active: bool = True
    priority: int = 1

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResolutionJob(BaseModel):
    """Batch resolution job"""
    job_id: UUID = Field(default_factory=uuid4)
    job_name: str

    # Scope
    entity_type: EntityType
    source_systems: List[str] = Field(default_factory=list)
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

    # Progress
    total_records: int = 0
    processed_records: int = 0
    matches_found: int = 0
    auto_merged: int = 0
    pending_review: int = 0
    errors: int = 0

    # Status
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Created by
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EntityResolutionStatistics(BaseModel):
    """Statistics for entity resolution"""
    total_master_entities: int = 0
    total_source_records: int = 0
    unresolved_records: int = 0
    pending_review: int = 0
    auto_merge_rate: float = 0.0
    average_match_score: float = 0.0
    by_entity_type: Dict[str, int] = Field(default_factory=dict)
    by_source_system: Dict[str, int] = Field(default_factory=dict)
    matches_this_month: int = 0
    merges_this_month: int = 0
    splits_this_month: int = 0
    data_quality_score: float = 0.0
