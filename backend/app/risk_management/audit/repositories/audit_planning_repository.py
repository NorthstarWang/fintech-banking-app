"""Audit Planning Repository - Data access for audit planning"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.audit_planning_models import (
    AuditUniverse, AnnualAuditPlan, PlannedAudit, RiskAssessment,
    AuditResource, ResourceAllocation, AuditBudget, QualityAssurance
)


class AuditPlanningRepository:
    def __init__(self):
        self._universe: Dict[UUID, AuditUniverse] = {}
        self._annual_plans: Dict[UUID, AnnualAuditPlan] = {}
        self._planned_audits: Dict[UUID, PlannedAudit] = {}
        self._risk_assessments: Dict[UUID, RiskAssessment] = {}
        self._resources: Dict[UUID, AuditResource] = {}
        self._allocations: Dict[UUID, ResourceAllocation] = {}
        self._budgets: Dict[UUID, AuditBudget] = {}
        self._qa_reviews: Dict[UUID, QualityAssurance] = {}

    async def save_universe_entity(self, entity: AuditUniverse) -> None:
        self._universe[entity.universe_id] = entity

    async def find_universe_entity_by_id(self, entity_id: UUID) -> Optional[AuditUniverse]:
        return self._universe.get(entity_id)

    async def find_all_universe_entities(self) -> List[AuditUniverse]:
        return list(self._universe.values())

    async def find_high_risk_entities(self) -> List[AuditUniverse]:
        return [e for e in self._universe.values() if e.risk_rating == "high"]

    async def save_annual_plan(self, plan: AnnualAuditPlan) -> None:
        self._annual_plans[plan.plan_id] = plan

    async def find_annual_plan_by_id(self, plan_id: UUID) -> Optional[AnnualAuditPlan]:
        return self._annual_plans.get(plan_id)

    async def find_all_annual_plans(self) -> List[AnnualAuditPlan]:
        return list(self._annual_plans.values())

    async def find_plan_by_year(self, year: int) -> Optional[AnnualAuditPlan]:
        for p in self._annual_plans.values():
            if p.plan_year == year:
                return p
        return None

    async def save_planned_audit(self, audit: PlannedAudit) -> None:
        self._planned_audits[audit.planned_audit_id] = audit

    async def find_planned_audit_by_id(self, audit_id: UUID) -> Optional[PlannedAudit]:
        return self._planned_audits.get(audit_id)

    async def find_planned_audits_by_plan(self, plan_id: UUID) -> List[PlannedAudit]:
        return [a for a in self._planned_audits.values() if a.plan_id == plan_id]

    async def save_risk_assessment(self, assessment: RiskAssessment) -> None:
        self._risk_assessments[assessment.assessment_id] = assessment

    async def find_risk_assessment_by_id(self, assessment_id: UUID) -> Optional[RiskAssessment]:
        return self._risk_assessments.get(assessment_id)

    async def find_assessments_by_entity(self, entity_id: UUID) -> List[RiskAssessment]:
        return [a for a in self._risk_assessments.values() if a.universe_entity_id == entity_id]

    async def save_resource(self, resource: AuditResource) -> None:
        self._resources[resource.resource_id] = resource

    async def find_resource_by_id(self, resource_id: UUID) -> Optional[AuditResource]:
        return self._resources.get(resource_id)

    async def find_all_resources(self) -> List[AuditResource]:
        return list(self._resources.values())

    async def find_available_resources(self) -> List[AuditResource]:
        return [r for r in self._resources.values() if r.hours_remaining > 0 and r.is_active]

    async def save_allocation(self, allocation: ResourceAllocation) -> None:
        self._allocations[allocation.allocation_id] = allocation

    async def find_allocation_by_id(self, allocation_id: UUID) -> Optional[ResourceAllocation]:
        return self._allocations.get(allocation_id)

    async def find_allocations_by_audit(self, audit_id: UUID) -> List[ResourceAllocation]:
        return [a for a in self._allocations.values() if a.planned_audit_id == audit_id]

    async def save_budget(self, budget: AuditBudget) -> None:
        self._budgets[budget.budget_id] = budget

    async def find_budget_by_id(self, budget_id: UUID) -> Optional[AuditBudget]:
        return self._budgets.get(budget_id)

    async def find_budget_by_plan(self, plan_id: UUID) -> Optional[AuditBudget]:
        for b in self._budgets.values():
            if b.plan_id == plan_id:
                return b
        return None

    async def save_qa(self, qa: QualityAssurance) -> None:
        self._qa_reviews[qa.qa_id] = qa

    async def find_qa_by_id(self, qa_id: UUID) -> Optional[QualityAssurance]:
        return self._qa_reviews.get(qa_id)

    async def find_all_qa_reviews(self) -> List[QualityAssurance]:
        return list(self._qa_reviews.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_universe_entities": len(self._universe),
            "high_risk_entities": len([e for e in self._universe.values() if e.risk_rating == "high"]),
            "total_annual_plans": len(self._annual_plans),
            "total_planned_audits": len(self._planned_audits),
            "total_risk_assessments": len(self._risk_assessments),
            "total_resources": len(self._resources),
            "available_resources": len([r for r in self._resources.values() if r.hours_remaining > 0]),
            "total_allocations": len(self._allocations),
            "total_budgets": len(self._budgets),
            "total_qa_reviews": len(self._qa_reviews),
        }


audit_planning_repository = AuditPlanningRepository()
