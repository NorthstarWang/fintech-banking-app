"""Compliance Testing API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.compliance_testing_models import TestingType
from ..services.compliance_testing_service import compliance_testing_service

router = APIRouter(prefix="/compliance-testing", tags=["Compliance Testing"])


class TestPlanCreateRequest(BaseModel):
    plan_name: str
    testing_period: str
    regulation: str
    requirement_reference: str
    test_objective: str
    test_procedure: str
    testing_type: TestingType
    sample_methodology: str
    planned_sample_size: int
    testing_frequency: str
    assigned_tester: str
    planned_date: date


class TestExecutionRequest(BaseModel):
    plan_id: UUID
    tester: str
    population_size: int
    sample_size: int
    items_tested: int
    exceptions_found: int
    evidence_references: List[str]
    observations: str
    conclusion: str


class ExceptionRequest(BaseModel):
    execution_id: UUID
    description: str
    sample_item: str
    expected_result: str
    actual_result: str
    severity: str
    impact: str


class RegulatoryChangeRequest(BaseModel):
    regulation: str
    regulator: str
    change_type: str
    effective_date: date
    summary: str
    detailed_description: str
    impact_assessment: str
    affected_areas: List[str]
    assigned_to: str
    implementation_deadline: date


@router.post("/test-plans", response_model=dict)
async def create_test_plan(request: TestPlanCreateRequest):
    plan = await compliance_testing_service.create_test_plan(
        plan_name=request.plan_name, testing_period=request.testing_period,
        regulation=request.regulation, requirement_reference=request.requirement_reference,
        test_objective=request.test_objective, test_procedure=request.test_procedure,
        testing_type=request.testing_type, sample_methodology=request.sample_methodology,
        planned_sample_size=request.planned_sample_size, testing_frequency=request.testing_frequency,
        assigned_tester=request.assigned_tester, planned_date=request.planned_date
    )
    return {"plan_id": str(plan.plan_id), "plan_reference": plan.plan_reference}


@router.get("/test-plans", response_model=List[dict])
async def list_test_plans(pending_only: bool = False):
    if pending_only:
        plans = await compliance_testing_service.repository.find_pending_test_plans()
    else:
        plans = await compliance_testing_service.repository.find_all_test_plans()
    return [{"plan_id": str(p.plan_id), "plan_reference": p.plan_reference, "plan_name": p.plan_name, "status": p.status} for p in plans]


@router.post("/executions", response_model=dict)
async def execute_test(request: TestExecutionRequest):
    execution = await compliance_testing_service.execute_test(
        plan_id=request.plan_id, tester=request.tester,
        population_size=request.population_size, sample_size=request.sample_size,
        items_tested=request.items_tested, exceptions_found=request.exceptions_found,
        evidence_references=request.evidence_references, observations=request.observations,
        conclusion=request.conclusion
    )
    return {"execution_id": str(execution.execution_id), "test_result": execution.test_result.value}


@router.get("/executions", response_model=List[dict])
async def list_executions(failed_only: bool = False):
    if failed_only:
        executions = await compliance_testing_service.repository.find_failed_executions()
    else:
        executions = await compliance_testing_service.repository.find_all_executions()
    return [{"execution_id": str(e.execution_id), "test_result": e.test_result.value, "exception_rate": float(e.exception_rate)} for e in executions]


@router.post("/exceptions", response_model=dict)
async def record_exception(request: ExceptionRequest):
    exception = await compliance_testing_service.record_exception(
        execution_id=request.execution_id, description=request.description,
        sample_item=request.sample_item, expected_result=request.expected_result,
        actual_result=request.actual_result, severity=request.severity, impact=request.impact
    )
    return {"exception_id": str(exception.exception_id), "exception_reference": exception.exception_reference}


@router.get("/exceptions", response_model=List[dict])
async def list_exceptions(open_only: bool = False):
    if open_only:
        exceptions = await compliance_testing_service.repository.find_open_exceptions()
    else:
        exceptions = await compliance_testing_service.repository.find_all_exceptions()
    return [{"exception_id": str(e.exception_id), "exception_reference": e.exception_reference, "severity": e.severity, "status": e.status} for e in exceptions]


@router.post("/exceptions/{exception_id}/remediate", response_model=dict)
async def remediate_exception(
    exception_id: UUID,
    root_cause: str = Query(...),
    remediation_action: str = Query(...),
    remediation_owner: str = Query(...),
    remediation_due_date: date = Query(...)
):
    exception = await compliance_testing_service.remediate_exception(
        exception_id, root_cause, remediation_action, remediation_owner, remediation_due_date
    )
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    return {"exception_id": str(exception.exception_id), "status": exception.status}


@router.post("/regulatory-changes", response_model=dict)
async def record_regulatory_change(request: RegulatoryChangeRequest):
    change = await compliance_testing_service.record_regulatory_change(
        regulation=request.regulation, regulator=request.regulator, change_type=request.change_type,
        effective_date=request.effective_date, summary=request.summary,
        detailed_description=request.detailed_description, impact_assessment=request.impact_assessment,
        affected_areas=request.affected_areas, assigned_to=request.assigned_to,
        implementation_deadline=request.implementation_deadline
    )
    return {"change_id": str(change.change_id), "change_reference": change.change_reference}


@router.get("/regulatory-changes", response_model=List[dict])
async def list_regulatory_changes(pending_only: bool = False):
    if pending_only:
        changes = await compliance_testing_service.repository.find_pending_regulatory_changes()
    else:
        changes = await compliance_testing_service.repository.find_all_regulatory_changes()
    return [{"change_id": str(c.change_id), "change_reference": c.change_reference, "regulation": c.regulation, "status": c.status} for c in changes]


@router.get("/statistics", response_model=dict)
async def get_compliance_testing_statistics():
    return await compliance_testing_service.get_statistics()
