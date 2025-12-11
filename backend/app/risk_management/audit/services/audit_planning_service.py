"""Audit Planning Service - Business logic for audit planning and resource management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.audit_planning_models import (
    AuditUniverse, AnnualAuditPlan, PlannedAudit, RiskAssessment,
    AuditResource, ResourceAllocation, AuditBudget, QualityAssurance
)
from ..repositories.audit_planning_repository import audit_planning_repository


class AuditPlanningService:
    def __init__(self):
        self.repository = audit_planning_repository

    async def add_to_universe(
        self, entity_code: str, entity_name: str, entity_type: str,
        description: str, owner: str, risk_rating: str,
        audit_frequency: str, regulatory_coverage: List[str],
        key_risks: List[str], key_controls: List[str]
    ) -> AuditUniverse:
        entity = AuditUniverse(
            entity_code=entity_code, entity_name=entity_name, entity_type=entity_type,
            description=description, owner=owner, risk_rating=risk_rating,
            audit_frequency=audit_frequency, regulatory_coverage=regulatory_coverage,
            key_risks=key_risks, key_controls=key_controls
        )
        await self.repository.save_universe_entity(entity)
        return entity

    async def assess_risk(
        self, universe_entity_id: UUID, assessor: str, assessment_type: str,
        risk_factors: List[Dict[str, Any]], factor_weights: Dict[str, Decimal],
        factor_scores: Dict[str, Decimal], control_factors: List[Dict[str, Any]],
        control_score: Decimal
    ) -> RiskAssessment:
        inherent_risk = sum(
            factor_weights.get(k, Decimal("1")) * v
            for k, v in factor_scores.items()
        ) / len(factor_scores) if factor_scores else Decimal("0")

        residual_risk = inherent_risk * (Decimal("100") - control_score) / Decimal("100")

        if residual_risk >= 70:
            rating = "high"
        elif residual_risk >= 40:
            rating = "medium"
        else:
            rating = "low"

        assessment = RiskAssessment(
            universe_entity_id=universe_entity_id, assessment_date=date.today(),
            assessor=assessor, assessment_type=assessment_type, risk_factors=risk_factors,
            factor_weights=factor_weights, factor_scores=factor_scores,
            inherent_risk_score=inherent_risk, control_factors=control_factors,
            control_score=control_score, residual_risk_score=residual_risk,
            risk_rating=rating,
            next_assessment_date=date(date.today().year + 1, date.today().month, date.today().day)
        )
        await self.repository.save_risk_assessment(assessment)

        entity = await self.repository.find_universe_entity_by_id(universe_entity_id)
        if entity:
            entity.risk_rating = rating
            entity.residual_risk_score = residual_risk

        return assessment

    async def create_annual_plan(
        self, plan_year: int, plan_name: str, prepared_by: str,
        total_hours: int, total_budget: Decimal, assumptions: List[str],
        constraints: List[str]
    ) -> AnnualAuditPlan:
        plan = AnnualAuditPlan(
            plan_year=plan_year, plan_name=plan_name, version="1.0",
            prepared_by=prepared_by, preparation_date=date.today(),
            total_hours=total_hours, total_budget=total_budget,
            assumptions=assumptions, constraints=constraints
        )
        await self.repository.save_annual_plan(plan)
        return plan

    async def add_planned_audit(
        self, plan_id: UUID, universe_entity_id: UUID, audit_name: str,
        audit_type: str, risk_rating: str, priority: int, planned_quarter: int,
        planned_start_date: date, planned_end_date: date, estimated_hours: int,
        scope_summary: str, objectives: List[str]
    ) -> PlannedAudit:
        audit = PlannedAudit(
            plan_id=plan_id, universe_entity_id=universe_entity_id, audit_name=audit_name,
            audit_type=audit_type, risk_rating=risk_rating, priority=priority,
            planned_quarter=planned_quarter, planned_start_date=planned_start_date,
            planned_end_date=planned_end_date, estimated_hours=estimated_hours,
            scope_summary=scope_summary, objectives=objectives
        )
        await self.repository.save_planned_audit(audit)

        plan = await self.repository.find_annual_plan_by_id(plan_id)
        if plan:
            plan.total_audits += 1

        return audit

    async def register_resource(
        self, employee_id: str, employee_name: str, role: str, department: str,
        certifications: List[str], expertise_areas: List[str],
        availability_percentage: Decimal, cost_rate: Decimal, total_hours_available: int
    ) -> AuditResource:
        resource = AuditResource(
            employee_id=employee_id, employee_name=employee_name, role=role,
            department=department, certifications=certifications,
            expertise_areas=expertise_areas, availability_percentage=availability_percentage,
            cost_rate=cost_rate, total_hours_available=total_hours_available,
            hours_remaining=total_hours_available
        )
        await self.repository.save_resource(resource)
        return resource

    async def allocate_resource(
        self, planned_audit_id: UUID, resource_id: UUID, role: str,
        allocated_hours: int, start_date: date, end_date: date
    ) -> ResourceAllocation:
        allocation = ResourceAllocation(
            planned_audit_id=planned_audit_id, resource_id=resource_id, role=role,
            allocated_hours=allocated_hours, start_date=start_date, end_date=end_date
        )
        await self.repository.save_allocation(allocation)

        resource = await self.repository.find_resource_by_id(resource_id)
        if resource:
            resource.hours_allocated += allocated_hours
            resource.hours_remaining = resource.total_hours_available - resource.hours_allocated

        return allocation

    async def create_budget(
        self, plan_id: UUID, budget_year: int, total_budget: Decimal,
        personnel_costs: Decimal, travel_costs: Decimal, technology_costs: Decimal,
        training_costs: Decimal, consulting_costs: Decimal, contingency: Decimal
    ) -> AuditBudget:
        budget = AuditBudget(
            plan_id=plan_id, budget_year=budget_year, total_budget=total_budget,
            personnel_costs=personnel_costs, travel_costs=travel_costs,
            technology_costs=technology_costs, training_costs=training_costs,
            consulting_costs=consulting_costs, contingency=contingency,
            other_costs=total_budget - personnel_costs - travel_costs - technology_costs - training_costs - consulting_costs - contingency
        )
        await self.repository.save_budget(budget)
        return budget

    async def conduct_qa_review(
        self, qa_type: str, review_period: str, reviewer: str,
        areas_reviewed: List[str], standards_assessed: List[str],
        findings: List[Dict[str, Any]], recommendations: List[str],
        overall_rating: str, conforms_to_standards: bool
    ) -> QualityAssurance:
        qa = QualityAssurance(
            qa_type=qa_type, review_period=review_period, reviewer=reviewer,
            review_date=date.today(), areas_reviewed=areas_reviewed,
            standards_assessed=standards_assessed, findings=findings,
            recommendations=recommendations, overall_rating=overall_rating,
            conforms_to_standards=conforms_to_standards,
            next_review_date=date(date.today().year + 1, date.today().month, date.today().day)
        )
        await self.repository.save_qa(qa)
        return qa

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


audit_planning_service = AuditPlanningService()
