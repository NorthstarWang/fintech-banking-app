"""
Watchlist Models

Defines data structures for internal and external watchlist management.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class WatchlistType(str, Enum):
    """Types of watchlists"""
    INTERNAL = "internal"
    EXTERNAL = "external"
    REGULATORY = "regulatory"
    LAW_ENFORCEMENT = "law_enforcement"
    INDUSTRY = "industry"


class WatchlistCategory(str, Enum):
    """Categories of watchlist entries"""
    HIGH_RISK = "high_risk"
    SUSPICIOUS = "suspicious"
    FRAUD = "fraud"
    SANCTIONS = "sanctions"
    PEP = "pep"
    ADVERSE_MEDIA = "adverse_media"
    TERRORIST = "terrorist"
    CRIMINAL = "criminal"
    DO_NOT_ONBOARD = "do_not_onboard"
    MONITOR_CLOSELY = "monitor_closely"
    EXITED = "exited"


class EntityIdentifier(BaseModel):
    """Entity identifier for matching"""
    identifier_type: str  # ssn, ein, passport, account_number, phone, email
    identifier_value: str
    issuing_country: Optional[str] = None
    is_primary: bool = False


class WatchlistEntry(BaseModel):
    """Entry in a watchlist"""
    entry_id: UUID = Field(default_factory=uuid4)
    watchlist_id: UUID

    # Entity information
    entity_type: str  # individual, organization
    primary_name: str
    aliases: List[str] = Field(default_factory=list)
    identifiers: List[EntityIdentifier] = Field(default_factory=list)

    # Personal details (for individuals)
    date_of_birth: Optional[date] = None
    nationalities: List[str] = Field(default_factory=list)
    countries_of_residence: List[str] = Field(default_factory=list)

    # Organization details
    registration_number: Optional[str] = None
    incorporation_country: Optional[str] = None

    # Category and risk
    category: WatchlistCategory
    risk_level: str = "high"
    risk_score: float = 0.0

    # Reason
    reason: str
    reason_code: Optional[str] = None
    evidence_summary: Optional[str] = None

    # Source
    source: str
    source_reference: Optional[str] = None
    source_date: Optional[datetime] = None

    # Related records
    related_case_ids: List[UUID] = Field(default_factory=list)
    related_alert_ids: List[UUID] = Field(default_factory=list)
    related_customer_ids: List[str] = Field(default_factory=list)

    # Status
    is_active: bool = True
    status: str = "active"  # active, inactive, under_review, removed

    # Review information
    last_reviewed_by: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[date] = None

    # Validity
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    # Created/Updated
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class Watchlist(BaseModel):
    """Watchlist definition"""
    watchlist_id: UUID = Field(default_factory=uuid4)
    watchlist_name: str
    watchlist_code: str
    watchlist_type: WatchlistType
    description: str

    # Configuration
    default_category: WatchlistCategory
    auto_alert: bool = True
    alert_severity: str = "high"

    # Access control
    owner_team: str
    view_teams: List[str] = Field(default_factory=list)
    edit_teams: List[str] = Field(default_factory=list)

    # Screening configuration
    include_in_screening: bool = True
    screening_priority: int = 1
    match_threshold: float = 0.8

    # Statistics
    entry_count: int = 0
    active_entry_count: int = 0

    # External source
    is_external: bool = False
    external_source_url: Optional[str] = None
    last_sync_date: Optional[datetime] = None
    sync_frequency_hours: int = 24

    # Status
    is_active: bool = True

    # Timestamps
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WatchlistMatch(BaseModel):
    """Match result when screening against watchlists"""
    match_id: UUID = Field(default_factory=uuid4)

    # What was screened
    screened_entity_type: str
    screened_entity_id: str
    screened_entity_name: str
    screened_identifiers: List[EntityIdentifier] = Field(default_factory=list)

    # Matched entry
    watchlist_id: UUID
    watchlist_name: str
    entry_id: UUID
    entry_name: str
    entry_category: WatchlistCategory

    # Match quality
    match_score: float
    match_type: str  # exact, fuzzy, partial
    matching_fields: List[str] = Field(default_factory=list)

    # Field-level scores
    name_score: float = 0.0
    identifier_score: float = 0.0
    dob_match: bool = False
    nationality_match: bool = False

    # Status
    status: str = "pending"  # pending, confirmed, false_positive, escalated
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    # Alert linkage
    alert_id: Optional[UUID] = None
    case_id: Optional[UUID] = None

    # Timestamps
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class WatchlistScreeningRequest(BaseModel):
    """Request to screen against watchlists"""
    request_id: UUID = Field(default_factory=uuid4)

    # Entity to screen
    entity_type: str
    entity_id: Optional[str] = None
    entity_name: str
    aliases: List[str] = Field(default_factory=list)
    identifiers: List[EntityIdentifier] = Field(default_factory=list)

    # Additional information
    date_of_birth: Optional[date] = None
    nationalities: List[str] = Field(default_factory=list)

    # Screening parameters
    watchlist_ids: Optional[List[UUID]] = None  # None = all active
    match_threshold: float = 0.8
    include_inactive: bool = False

    # Request metadata
    screening_type: str = "real_time"  # real_time, batch, periodic
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class WatchlistScreeningResult(BaseModel):
    """Result of watchlist screening"""
    result_id: UUID = Field(default_factory=uuid4)
    request_id: UUID

    # Screened entity
    entity_type: str
    entity_id: Optional[str] = None
    entity_name: str

    # Results
    has_matches: bool = False
    match_count: int = 0
    highest_match_score: float = 0.0
    matches: List[WatchlistMatch] = Field(default_factory=list)

    # Lists screened
    watchlists_screened: int = 0
    entries_screened: int = 0

    # Processing
    screening_date: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0

    # Actions taken
    alerts_generated: int = 0
    alert_ids: List[UUID] = Field(default_factory=list)


class WatchlistImport(BaseModel):
    """Watchlist import record"""
    import_id: UUID = Field(default_factory=uuid4)
    watchlist_id: UUID

    # Import source
    source_type: str  # file, api, database
    source_name: str
    source_reference: Optional[str] = None

    # Statistics
    total_records: int = 0
    imported_records: int = 0
    updated_records: int = 0
    failed_records: int = 0
    duplicate_records: int = 0

    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Status
    status: str = "pending"  # pending, processing, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Created by
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WatchlistAuditLog(BaseModel):
    """Audit log for watchlist changes"""
    audit_id: UUID = Field(default_factory=uuid4)
    watchlist_id: UUID
    entry_id: Optional[UUID] = None

    # Action
    action: str  # create, update, delete, review, activate, deactivate
    action_details: str

    # Changes
    previous_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

    # Actor
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)

    # Context
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class WatchlistStatistics(BaseModel):
    """Watchlist statistics"""
    total_watchlists: int = 0
    total_entries: int = 0
    active_entries: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)
    matches_this_month: int = 0
    false_positive_rate: float = 0.0
    pending_review: int = 0
    entries_added_this_month: int = 0
    entries_removed_this_month: int = 0
