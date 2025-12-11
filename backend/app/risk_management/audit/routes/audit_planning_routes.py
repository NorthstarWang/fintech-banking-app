"""Audit Planning API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..services.audit_planning_service import audit_planning_service

router = APIRouter(prefix="/audit-planning", tags=["Audit Planning"])


class UniverseEntityRequest(BaseModel):
    entity_code: str
    entity_name: str
    entity_type: str
    description: str
    owner: str
    risk_rating: str
    audit_frequency: str
    regulatory_coverage: List[str]
    key_risks: List[str]
    key_controls: List[str]


class RiskAssessmentRequest(BaseModel):
    universe_entity_id: UUID
    assessor: str
    assessment_type: str
    risk_factors: List[Dict[str, Any]]
    factor_weights: Dict[str, Decimal]
    factor_scores: Dict[str, Decimal]
    control_factors: List[Dict[str, Any]]
    control_score: Decimal


class AnnualPlanRequest(BaseModel):
    plan_year: int
    plan_name: str
    prepared_by: str
    total_hours: int
    total_budget: Decimal
    assumptions: List[str]
    constraints: List[str]


class PlannedAuditRequest(BaseModel):
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
    scope_summary: str
    objectives: List[str]


class ResourceRequest(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    department: str
    certifications: List[str]
    expertise_areas: List[str]
    availability_percentage: Decimal
    cost_rate: Decimal
    total_hours_available: int


class AllocationRequest(BaseModel):
    planned_audit_id: UUID
    resource_id: UUID
    role: str
    allocated_hours: int
    start_date: date
    end_date: date


class BudgetRequest(BaseModel):
    plan_id: UUID
    budget_year: int
    total_budget: Decimal
    personnel_costs: Decimal
    travel_costs: Decimal
    technology_costs: Decimal
    training_costs: Decimal
    consulting_costs: Decimal
    contingency: Decimal


@router.post("/universe", response_model=dict)
async def add_to_universe(request: UniverseEntityRequest):
    entity = await audit_planning_service.add_to_universe(
        entity_code=request.entity_code, entity_name=request.entity_name,
        entity_type=request.entity_type, description=request.description,
        owner=request.owner, risk_rating=request.risk_rating,
        audit_frequency=request.audit_frequency, regulatory_coverage=request.regulatory_coverage,
        key_risks=request.key_risks, key_controls=request.key_controls
    )
    return {"universe_id": str(entity.universe_id), "entity_code": entity.entity_code}


@router.get("/universe", response_model=List[dict])
async def list_universe_entities(high_risk_only: bool = False):
    if high_risk_only:
        entities = await audit_planning_service.repository.find_high_risk_entities()
    else:
        entities = await audit_planning_service.repository.find_all_universe_entities()
    return [{"universe_id": str(e.universe_id), "entity_code": e.entity_code, "entity_name": e.entity_name, "risk_rating": e.risk_rating} for e in entities]


@router.post("/risk-assessments", response_model=dict)
async def assess_risk(request: RiskAssessmentRequest):
    assessment = await audit_planning_service.assess_risk(
        universe_entity_id=request.universe_entity_id, assessor=request.assessor,
        assessment_type=request.assessment_type, risk_factors=request.risk_factors,
        factor_weights=request.factor_weights, factor_scores=request.factor_scores,
        control_factors=request.control_factors, control_score=request.control_score
    )
    return {"assessment_id": str(assessment.assessment_id), "risk_rating": assessment.risk_rating, "residual_risk_score": float(assessment.residual_risk_score)}


@router.get("/risk-assessments/{entity_id}", response_model=List[dict])
async def get_entity_assessments(entity_id: UUID):
    assessments = await audit_planning_service.repository.find_assessments_by_entity(entity_id)
    return [{"assessment_id": str(a.assessment_id), "risk_rating": a.risk_rating, "assessment_date": str(a.assessment_date)} for a in assessments]


@router.post("/annual-plans", response_model=dict)
async def create_annual_plan(request: AnnualPlanRequest):
    plan = await audit_planning_service.create_annual_plan(
        plan_year=request.plan_year, plan_name=request.plan_name, prepared_by=request.prepared_by,
        total_hours=request.total_hours, total_budget=request.total_budget,
        assumptions=request.assumptions, constraints=request.constraints
    )
    return {"plan_id": str(plan.plan_id), "plan_year": plan.plan_year}


@router.get("/annual-plans", response_model=List[dict])
async def list_annual_plans():
    plans = await audit_planning_service.repository.find_all_annual_plans()
    return [{"plan_id": str(p.plan_id), "plan_name": p.plan_name, "plan_year": p.plan_year, "status": p.status} for p in plans]


@router.post("/planned-audits", response_model=dict)
async def add_planned_audit(request: PlannedAuditRequest):
    audit = await audit_planning_service.add_planned_audit(
        plan_id=request.plan_id, universe_entity_id=request.universe_entity_id,
        audit_name=request.audit_name, audit_type=request.audit_type,
        risk_rating=request.risk_rating, priority=request.priority,
        planned_quarter=request.planned_quarter, planned_start_date=request.planned_start_date,
        planned_end_date=request.planned_end_date, estimated_hours=request.estimated_hours,
        scope_summary=request.scope_summary, objectives=request.objectives
    )
    return {"planned_audit_id": str(audit.planned_audit_id), "audit_name": audit.audit_name}


@router.get("/annual-plans/{plan_id}/audits", response_model=List[dict])
async def get_plan_audits(plan_id: UUID):
    audits = await audit_planning_service.repository.find_planned_audits_by_plan(plan_id)
    return [{"planned_audit_id": str(a.planned_audit_id), "audit_name": a.audit_name, "planned_quarter": a.planned_quarter, "status": a.status} for a in audits]


@router.post("/resources", response_model=dict)
async def register_resource(request: ResourceRequest):
    resource = await audit_planning_service.register_resource(
        employee_id=request.employee_id, employee_name=request.employee_name,
        role=request.role, department=request.department, certifications=request.certifications,
        expertise_areas=request.expertise_areas, availability_percentage=request.availability_percentage,
        cost_rate=request.cost_rate, total_hours_available=request.total_hours_available
    )
    return {"resource_id": str(resource.resource_id), "employee_name": resource.employee_name}


@router.get("/resources", response_model=List[dict])
async def list_resources(available_only: bool = False):
    if available_only:
        resources = await audit_planning_service.repository.find_available_resources()
    else:
        resources = await audit_planning_service.repository.find_all_resources()
    return [{"resource_id": str(r.resource_id), "employee_name": r.employee_name, "role": r.role, "hours_remaining": r.hours_remaining} for r in resources]


@router.post("/allocations", response_model=dict)
async def allocate_resource(request: AllocationRequest):
    allocation = await audit_planning_service.allocate_resource(
        planned_audit_id=request.planned_audit_id, resource_id=request.resource_id,
        role=request.role, allocated_hours=request.allocated_hours,
        start_date=request.start_date, end_date=request.end_date
    )
    return {"allocation_id": str(allocation.allocation_id)}


@router.post("/budgets", response_model=dict)
async def create_budget(request: BudgetRequest):
    budget = await audit_planning_service.create_budget(
        plan_id=request.plan_id, budget_year=request.budget_year, total_budget=request.total_budget,
        personnel_costs=request.personnel_costs, travel_costs=request.travel_costs,
        technology_costs=request.technology_costs, training_costs=request.training_costs,
        consulting_costs=request.consulting_costs, contingency=request.contingency
    )
    return {"budget_id": str(budget.budget_id)}


@router.get("/statistics", response_model=dict)
async def get_audit_planning_statistics():
    return await audit_planning_service.get_statistics()
