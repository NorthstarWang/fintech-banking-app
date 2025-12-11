"""Business Continuity Models - Data models for BCP/DR management"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum


class BCPStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    RETIRED = "retired"


class CriticalityLevel(str, Enum):
    MISSION_CRITICAL = "mission_critical"
    CRITICAL = "critical"
    ESSENTIAL = "essential"
    NON_ESSENTIAL = "non_essential"


class DisasterType(str, Enum):
    NATURAL = "natural"
    TECHNOLOGY = "technology"
    CYBER = "cyber"
    PANDEMIC = "pandemic"
    CIVIL = "civil"
    UTILITY = "utility"
    SUPPLY_CHAIN = "supply_chain"


class RecoveryStrategy(str, Enum):
    HOT_SITE = "hot_site"
    WARM_SITE = "warm_site"
    COLD_SITE = "cold_site"
    CLOUD = "cloud"
    WORK_FROM_HOME = "work_from_home"
    MUTUAL_AID = "mutual_aid"


class TestType(str, Enum):
    TABLETOP = "tabletop"
    WALKTHROUGH = "walkthrough"
    SIMULATION = "simulation"
    PARALLEL = "parallel"
    FULL_INTERRUPTION = "full_interruption"


class BusinessProcess(BaseModel):
    process_id: UUID = Field(default_factory=uuid4)
    process_name: str
    process_description: str
    business_unit: str
    process_owner: str
    criticality: CriticalityLevel
    rto_hours: int  # Recovery Time Objective
    rpo_hours: int  # Recovery Point Objective
    mtpd_hours: int  # Maximum Tolerable Period of Disruption
    minimum_staff: int
    normal_staff: int
    dependencies: List[str] = Field(default_factory=list)
    systems_required: List[str] = Field(default_factory=list)
    vendors_required: List[str] = Field(default_factory=list)
    alternate_location: Optional[str] = None
    recovery_strategy: RecoveryStrategy
    financial_impact_per_hour: Decimal
    regulatory_impact: bool = False
    customer_impact: bool = False
    is_active: bool = True


class BusinessContinuityPlan(BaseModel):
    plan_id: UUID = Field(default_factory=uuid4)
    plan_name: str
    plan_version: str
    business_unit: str
    plan_owner: str
    status: BCPStatus = BCPStatus.DRAFT
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    approved_by: Optional[str] = None
    approval_date: Optional[date] = None
    scope: str
    objectives: List[str]
    assumptions: List[str]
    processes_covered: List[UUID] = Field(default_factory=list)
    recovery_teams: List[Dict[str, Any]] = Field(default_factory=list)
    communication_plan: Dict[str, Any] = Field(default_factory=dict)
    activation_criteria: List[str] = Field(default_factory=list)
    deactivation_criteria: List[str] = Field(default_factory=list)
    document_location: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DisasterRecoveryPlan(BaseModel):
    dr_plan_id: UUID = Field(default_factory=uuid4)
    plan_name: str
    plan_version: str
    status: BCPStatus = BCPStatus.DRAFT
    system_name: str
    system_criticality: CriticalityLevel
    rto_hours: int
    rpo_hours: int
    recovery_site: str
    recovery_strategy: RecoveryStrategy
    backup_frequency: str
    backup_location: str
    backup_retention: str
    recovery_procedures: List[str] = Field(default_factory=list)
    verification_steps: List[str] = Field(default_factory=list)
    contact_list: List[Dict[str, str]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    last_test_date: Optional[date] = None
    next_test_date: Optional[date] = None
    test_result: Optional[str] = None
    owner: str
    approved_by: Optional[str] = None


class BCPTest(BaseModel):
    test_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    test_name: str
    test_type: TestType
    test_date: date
    test_duration_hours: float
    scope: str
    objectives: List[str]
    participants: List[str]
    scenarios_tested: List[str]
    test_coordinator: str
    test_result: str  # pass, partial, fail
    rto_achieved: Optional[int] = None
    rpo_achieved: Optional[int] = None
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    report_date: Optional[date] = None
    approved_by: Optional[str] = None


class BCPIncident(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    incident_name: str
    disaster_type: DisasterType
    declaration_time: datetime
    declared_by: str
    affected_locations: List[str]
    affected_processes: List[UUID]
    impact_description: str
    plan_activated: UUID
    activation_time: datetime
    recovery_start_time: Optional[datetime] = None
    recovery_end_time: Optional[datetime] = None
    deactivation_time: Optional[datetime] = None
    status: str = "active"
    actual_rto_hours: Optional[float] = None
    actual_rpo_hours: Optional[float] = None
    financial_impact: Optional[Decimal] = None
    lessons_learned: List[str] = Field(default_factory=list)
    post_incident_review_date: Optional[date] = None


class CrisisTeamMember(BaseModel):
    member_id: UUID = Field(default_factory=uuid4)
    team_name: str
    role: str
    primary_contact: str
    primary_phone: str
    primary_email: str
    alternate_contact: Optional[str] = None
    alternate_phone: Optional[str] = None
    backup_person: Optional[str] = None
    backup_phone: Optional[str] = None
    responsibilities: List[str]
    is_active: bool = True


class BCPMetrics(BaseModel):
    metrics_id: UUID = Field(default_factory=uuid4)
    metrics_date: date
    business_unit: Optional[str] = None
    total_processes: int
    critical_processes: int
    plans_count: int
    plans_approved: int
    plans_expired: int
    tests_conducted_ytd: int
    tests_passed: int
    average_rto_achievement: Decimal
    average_rpo_achievement: Decimal
    incidents_ytd: int
    successful_recoveries: int
    open_action_items: int
    overdue_reviews: int
    coverage_percentage: Decimal
    generated_at: datetime = Field(default_factory=datetime.utcnow)
