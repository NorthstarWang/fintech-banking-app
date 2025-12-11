"""
Sanctions Screening Models

Defines data structures for sanctions list screening and management.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SanctionListType(str, Enum):
    """Types of sanction lists"""
    OFAC_SDN = "ofac_sdn"
    OFAC_CONSOLIDATED = "ofac_consolidated"
    UN_CONSOLIDATED = "un_consolidated"
    EU_CONSOLIDATED = "eu_consolidated"
    UK_HMT = "uk_hmt"
    FATF_HIGH_RISK = "fatf_high_risk"
    PEP_LIST = "pep_list"
    ADVERSE_MEDIA = "adverse_media"
    INTERNAL_WATCHLIST = "internal_watchlist"
    INTERPOL = "interpol"
    FBI_MOST_WANTED = "fbi_most_wanted"


class MatchStatus(str, Enum):
    """Status of a sanctions match"""
    PENDING_REVIEW = "pending_review"
    CONFIRMED_MATCH = "confirmed_match"
    FALSE_POSITIVE = "false_positive"
    POTENTIAL_MATCH = "potential_match"
    ESCALATED = "escalated"


class EntityType(str, Enum):
    """Type of sanctioned entity"""
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"
    VESSEL = "vessel"
    AIRCRAFT = "aircraft"
    PROPERTY = "property"


class SanctionListEntry(BaseModel):
    """Entry in a sanctions list"""
    entry_id: UUID = Field(default_factory=uuid4)
    list_type: SanctionListType
    list_name: str

    # Entity information
    entity_type: EntityType
    primary_name: str
    aliases: List[str] = Field(default_factory=list)

    # Identification
    identifiers: Dict[str, str] = Field(default_factory=dict)  # passport, id_number, etc.

    # Location information
    addresses: List[Dict[str, str]] = Field(default_factory=list)
    nationalities: List[str] = Field(default_factory=list)
    countries_of_birth: List[str] = Field(default_factory=list)

    # Dates
    date_of_birth: Optional[date] = None
    date_of_birth_range: Optional[Dict[str, date]] = None
    place_of_birth: Optional[str] = None

    # Sanction details
    sanction_programs: List[str] = Field(default_factory=list)
    sanction_reasons: List[str] = Field(default_factory=list)
    listing_date: Optional[date] = None

    # Additional information
    remarks: Optional[str] = None
    source_url: Optional[str] = None

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class ScreeningRequest(BaseModel):
    """Request to screen an entity against sanctions lists"""
    request_id: UUID = Field(default_factory=uuid4)

    # Entity to screen
    entity_type: EntityType
    entity_id: Optional[str] = None
    entity_name: str
    aliases: List[str] = Field(default_factory=list)

    # Additional identifiers
    date_of_birth: Optional[date] = None
    nationalities: List[str] = Field(default_factory=list)
    addresses: List[Dict[str, str]] = Field(default_factory=list)
    identifiers: Dict[str, str] = Field(default_factory=dict)

    # Screening parameters
    lists_to_screen: List[SanctionListType] = Field(default_factory=list)
    match_threshold: float = 0.8
    fuzzy_matching: bool = True

    # Request metadata
    screening_type: str = "standard"  # standard, enhanced, batch
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = "normal"


class MatchDetail(BaseModel):
    """Details of a potential match"""
    match_id: UUID = Field(default_factory=uuid4)
    list_entry_id: UUID
    list_type: SanctionListType

    # Match quality
    match_score: float = Field(ge=0, le=1)
    match_algorithm: str

    # Field-level matches
    name_match_score: float
    name_match_type: str  # exact, fuzzy, alias
    dob_match: bool = False
    nationality_match: bool = False
    address_match: bool = False
    identifier_matches: List[str] = Field(default_factory=list)

    # Matched entity details
    matched_name: str
    matched_aliases: List[str] = Field(default_factory=list)
    matched_identifiers: Dict[str, str] = Field(default_factory=dict)
    sanction_programs: List[str] = Field(default_factory=list)


class ScreeningResult(BaseModel):
    """Result of a sanctions screening"""
    result_id: UUID = Field(default_factory=uuid4)
    request_id: UUID

    # Screened entity
    entity_type: EntityType
    entity_id: Optional[str] = None
    entity_name: str

    # Overall result
    has_matches: bool = False
    match_count: int = 0
    highest_match_score: float = 0.0

    # Individual matches
    matches: List[MatchDetail] = Field(default_factory=list)

    # Lists screened
    lists_screened: List[SanctionListType] = Field(default_factory=list)

    # Processing info
    screening_date: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0

    # Status
    status: MatchStatus = MatchStatus.PENDING_REVIEW
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class MatchReview(BaseModel):
    """Review of a potential sanctions match"""
    review_id: UUID = Field(default_factory=uuid4)
    result_id: UUID
    match_id: UUID

    # Review decision
    decision: MatchStatus
    decision_reason: str

    # Reviewer information
    reviewed_by: str
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)

    # Supporting evidence
    evidence_notes: Optional[str] = None
    supporting_documents: List[str] = Field(default_factory=list)

    # Escalation
    escalated: bool = False
    escalated_to: Optional[str] = None
    escalation_reason: Optional[str] = None


class SanctionAlert(BaseModel):
    """Alert generated from sanctions screening"""
    alert_id: UUID = Field(default_factory=uuid4)
    screening_result_id: UUID

    # Alert details
    alert_type: str
    severity: str
    status: str = "open"

    # Entity information
    entity_type: EntityType
    entity_id: Optional[str] = None
    entity_name: str

    # Match information
    match_list: SanctionListType
    match_score: float
    matched_name: str
    sanction_programs: List[str] = Field(default_factory=list)

    # Assignment
    assigned_to: Optional[str] = None

    # Resolution
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None


class BatchScreeningJob(BaseModel):
    """Batch screening job"""
    job_id: UUID = Field(default_factory=uuid4)

    # Job details
    job_name: str
    job_type: str  # customer_refresh, transaction_screening, new_list_import

    # Scope
    total_entities: int = 0
    lists_to_screen: List[SanctionListType] = Field(default_factory=list)

    # Progress
    entities_processed: int = 0
    matches_found: int = 0
    errors_count: int = 0

    # Status
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Configuration
    match_threshold: float = 0.8
    parallel_workers: int = 4

    # Created by
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SanctionListUpdate(BaseModel):
    """Update to a sanctions list"""
    update_id: UUID = Field(default_factory=uuid4)
    list_type: SanctionListType

    # Update details
    update_type: str  # full_refresh, incremental
    source_url: str
    source_date: datetime

    # Statistics
    total_entries: int = 0
    new_entries: int = 0
    modified_entries: int = 0
    removed_entries: int = 0

    # Processing
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: int = 0
    errors: List[str] = Field(default_factory=list)

    # Status
    status: str = "completed"
    applied: bool = True


class WatchlistEntry(BaseModel):
    """Internal watchlist entry"""
    entry_id: UUID = Field(default_factory=uuid4)

    # Entity information
    entity_type: EntityType
    entity_name: str
    aliases: List[str] = Field(default_factory=list)
    identifiers: Dict[str, str] = Field(default_factory=dict)

    # Watchlist details
    reason: str
    risk_level: str
    added_by: str
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # Validity
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    is_active: bool = True

    # Review
    last_reviewed: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    next_review: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None
    related_case_ids: List[UUID] = Field(default_factory=list)
