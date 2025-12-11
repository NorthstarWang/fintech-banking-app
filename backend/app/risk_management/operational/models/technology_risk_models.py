"""Technology Risk Models - Data models for IT risk management"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class AssetType(str, Enum):
    APPLICATION = "application"
    DATABASE = "database"
    SERVER = "server"
    NETWORK = "network"
    ENDPOINT = "endpoint"
    CLOUD_SERVICE = "cloud_service"
    DATA = "data"


class AssetCriticality(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class VulnerabilitySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class PatchStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    FAILED = "failed"
    DEFERRED = "deferred"
    NOT_APPLICABLE = "not_applicable"


class IncidentType(str, Enum):
    SECURITY = "security"
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    CONFIGURATION = "configuration"


class ITAsset(BaseModel):
    asset_id: UUID = Field(default_factory=uuid4)
    asset_code: str
    asset_name: str
    asset_type: AssetType
    description: str
    criticality: AssetCriticality
    owner: str
    custodian: str
    business_unit: str
    location: str
    environment: str  # production, staging, development
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    version: Optional[str] = None
    vendor: Optional[str] = None
    support_end_date: Optional[date] = None
    data_classification: str
    pii_stored: bool = False
    pci_scope: bool = False
    sox_scope: bool = False
    last_scan_date: Optional[date] = None
    vulnerability_count: int = 0
    compliance_status: str = "compliant"
    is_active: bool = True
    created_date: date = Field(default_factory=date.today)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Vulnerability(BaseModel):
    vulnerability_id: UUID = Field(default_factory=uuid4)
    cve_id: Optional[str] = None
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: Optional[Decimal] = None
    cvss_vector: Optional[str] = None
    affected_assets: List[UUID] = Field(default_factory=list)
    affected_systems: List[str] = Field(default_factory=list)
    discovery_date: date
    discovery_source: str
    exploit_available: bool = False
    actively_exploited: bool = False
    patch_available: bool = False
    patch_id: Optional[str] = None
    remediation_steps: List[str] = Field(default_factory=list)
    workaround: Optional[str] = None
    status: str = "open"
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    remediation_date: Optional[date] = None
    false_positive: bool = False
    risk_accepted: bool = False
    acceptance_reason: Optional[str] = None
    acceptance_expiry: Optional[date] = None


class PatchManagement(BaseModel):
    patch_id: UUID = Field(default_factory=uuid4)
    patch_code: str
    patch_name: str
    vendor: str
    release_date: date
    severity: str
    affected_products: List[str]
    affected_assets: List[UUID] = Field(default_factory=list)
    cve_addressed: List[str] = Field(default_factory=list)
    status: PatchStatus = PatchStatus.PENDING
    scheduled_date: Optional[date] = None
    applied_date: Optional[date] = None
    applied_by: Optional[str] = None
    test_required: bool = True
    test_status: Optional[str] = None
    test_date: Optional[date] = None
    rollback_plan: bool = False
    change_ticket: Optional[str] = None
    notes: Optional[str] = None


class TechRiskAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    assessment_type: str
    assessment_date: date
    assessor: str
    confidentiality_risk: str
    integrity_risk: str
    availability_risk: str
    overall_risk_rating: str
    threats_identified: List[str]
    vulnerabilities_found: List[str]
    controls_in_place: List[str]
    control_gaps: List[str]
    recommendations: List[str]
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_assessment_date: Optional[date] = None
    status: str = "completed"
    approved_by: Optional[str] = None


class SecurityIncident(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    incident_number: str
    incident_type: IncidentType
    severity: str
    status: str = "open"
    title: str
    description: str
    detected_time: datetime
    reported_time: datetime
    affected_assets: List[UUID] = Field(default_factory=list)
    affected_users: int = 0
    data_compromised: bool = False
    data_type_compromised: Optional[List[str]] = None
    records_affected: Optional[int] = None
    attack_vector: Optional[str] = None
    indicators_of_compromise: List[str] = Field(default_factory=list)
    containment_time: Optional[datetime] = None
    eradication_time: Optional[datetime] = None
    recovery_time: Optional[datetime] = None
    closure_time: Optional[datetime] = None
    root_cause: Optional[str] = None
    lessons_learned: List[str] = Field(default_factory=list)
    regulatory_notification: bool = False
    notification_date: Optional[datetime] = None
    financial_impact: Optional[Decimal] = None


class AccessReview(BaseModel):
    review_id: UUID = Field(default_factory=uuid4)
    system_id: UUID
    system_name: str
    review_type: str  # periodic, ad_hoc
    review_date: date
    reviewer: str
    total_users: int
    users_reviewed: int
    access_confirmed: int
    access_revoked: int
    access_modified: int
    privileged_accounts: int
    service_accounts: int
    orphan_accounts: int
    dormant_accounts: int
    segregation_conflicts: int
    findings: List[str] = Field(default_factory=list)
    status: str = "in_progress"
    completion_date: Optional[date] = None
    next_review_date: Optional[date] = None


class ChangeRisk(BaseModel):
    change_id: UUID = Field(default_factory=uuid4)
    change_ticket: str
    change_title: str
    change_type: str  # standard, normal, emergency
    change_date: date
    affected_systems: List[UUID]
    risk_category: str
    risk_score: int
    impact_assessment: str
    rollback_plan: bool
    test_plan: bool
    approval_status: str
    approved_by: Optional[str] = None
    implementation_status: str
    post_implementation_review: bool = False
    issues_found: List[str] = Field(default_factory=list)
    created_by: str


class TechRiskMetrics(BaseModel):
    metrics_id: UUID = Field(default_factory=uuid4)
    metrics_date: date
    total_assets: int
    critical_assets: int
    assets_scanned: int
    scan_coverage: Decimal
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    vulnerabilities_remediated_mtd: int
    average_remediation_days: float
    patches_pending: int
    patches_overdue: int
    security_incidents_mtd: int
    mttr_hours: float  # Mean Time To Resolve
    access_reviews_completed: int
    access_reviews_pending: int
    compliance_score: Decimal
    generated_at: datetime = Field(default_factory=datetime.utcnow)
