"""Audit Planning Models"""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditUniverse(BaseModel):
    universe_id: UUID = Field(default_factory=uuid4)
    entity_code: str
    entity_name: str
    entity_type: str  # process, business_unit, system, location
    parent_entity: str | None = None
    description: str
    owner: str
    risk_rating: str = "medium"
    inherent_risk_score: Decimal = Decimal("0")
    control_environment_score: Decimal = Decimal("0")
    residual_risk_score: Decimal = Decimal("0")
    last_audit_date: date | None = None
    last_audit_rating: str = ""
    audit_frequency: str = "annual"
    next_audit_due: date | None = None
    regulatory_coverage: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    key_controls: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_date: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnnualAuditPlan(BaseModel):
    plan_id: UUID = Field(default_factory=uuid4)
    plan_year: int
    plan_name: str
    version: str
    prepared_by: str
    preparation_date: date
    approved_by: str | None = None
    approval_date: date | None = None
    total_audits: int = 0
    total_hours: int = 0
    total_budget: Decimal = Decimal("0")
    risk_coverage: dict[str, Decimal] = Field(default_factory=dict)
    regulatory_coverage: dict[str, int] = Field(default_factory=dict)
    resource_allocation: dict[str, int] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    status: str = "draft"


class PlannedAudit(BaseModel):
    planned_audit_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    universe_entity_id: UUID
    audit_name: str
    audit_type: str
    risk_rating: str
    priority: int
    planned_quarter: int
    planned_start_date: date
    planned_end_date: date
    estimated_hours: int
    lead_auditor: str = ""
    team_size: int = 1
    scope_summary: str = ""
    objectives: list[str] = Field(default_factory=list)
    regulatory_driver: list[str] = Field(default_factory=list)
    status: str = "planned"
    carryover_from_prior_year: bool = False


class RiskAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    universe_entity_id: UUID
    assessment_date: date
    assessor: str
    assessment_type: str  # annual, triggered, continuous
    risk_factors: list[dict[str, Any]] = Field(default_factory=list)
    factor_weights: dict[str, Decimal] = Field(default_factory=dict)
    factor_scores: dict[str, Decimal] = Field(default_factory=dict)
    inherent_risk_score: Decimal = Decimal("0")
    control_factors: list[dict[str, Any]] = Field(default_factory=list)
    control_score: Decimal = Decimal("0")
    residual_risk_score: Decimal = Decimal("0")
    risk_rating: str = "medium"
    key_risk_areas: list[str] = Field(default_factory=list)
    audit_recommendation: str = ""
    next_assessment_date: date
    status: str = "completed"


class AuditResource(BaseModel):
    resource_id: UUID = Field(default_factory=uuid4)
    employee_id: str
    employee_name: str
    role: str
    department: str
    certifications: list[str] = Field(default_factory=list)
    expertise_areas: list[str] = Field(default_factory=list)
    availability_percentage: Decimal = Decimal("100")
    cost_rate: Decimal = Decimal("0")
    total_hours_available: int = 0
    hours_allocated: int = 0
    hours_remaining: int = 0
    assignments: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class ResourceAllocation(BaseModel):
    allocation_id: UUID = Field(default_factory=uuid4)
    planned_audit_id: UUID
    resource_id: UUID
    role: str
    allocated_hours: int
    start_date: date
    end_date: date
    actual_hours: int = 0
    status: str = "allocated"
    notes: str = ""


class AuditBudget(BaseModel):
    budget_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    budget_year: int
    total_budget: Decimal
    personnel_costs: Decimal = Decimal("0")
    travel_costs: Decimal = Decimal("0")
    technology_costs: Decimal = Decimal("0")
    training_costs: Decimal = Decimal("0")
    consulting_costs: Decimal = Decimal("0")
    other_costs: Decimal = Decimal("0")
    contingency: Decimal = Decimal("0")
    approved_by: str | None = None
    approval_date: date | None = None
    actual_spend: Decimal = Decimal("0")
    variance: Decimal = Decimal("0")
    status: str = "draft"


class QualityAssurance(BaseModel):
    qa_id: UUID = Field(default_factory=uuid4)
    qa_type: str  # internal, external, peer_review
    review_period: str
    reviewer: str
    review_date: date
    areas_reviewed: list[str] = Field(default_factory=list)
    standards_assessed: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    overall_rating: str
    conforms_to_standards: bool = True
    improvement_actions: list[dict[str, Any]] = Field(default_factory=list)
    next_review_date: date
    status: str = "completed"
