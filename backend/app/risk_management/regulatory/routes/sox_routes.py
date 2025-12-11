"""SOX Compliance API Routes"""

from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.sox_models import ControlObjective, AssertionType
from ..services.sox_service import sox_service

router = APIRouter(prefix="/sox", tags=["SOX Compliance"])


class ProcessRegistrationRequest(BaseModel):
    process_name: str
    process_description: str
    business_unit: str
    process_owner: str
    financial_statement_areas: List[str]
    assertions_addressed: List[AssertionType]
    materiality_threshold: Decimal
    risk_rating: str
    documentation_location: str


class ControlCreateRequest(BaseModel):
    process_id: UUID
    control_name: str
    control_description: str
    control_objective: ControlObjective
    assertions: List[AssertionType]
    control_type: str
    control_nature: str
    control_frequency: str
    control_owner: str
    performer: str
    evidence_type: str
    evidence_retention: str
    key_control: bool = False


class TestPlanCreateRequest(BaseModel):
    fiscal_year: int
    quarter: int
    control_id: UUID
    test_type: str
    planned_test_date: date
    sample_size: int
    selection_method: str
    test_procedure: str
    assigned_tester: str


class TestResultRequest(BaseModel):
    plan_id: UUID
    control_id: UUID
    tester: str
    population_size: int
    sample_size: int
    items_tested: int
    exceptions_found: int
    test_evidence: List[str]


class CertificationRequest(BaseModel):
    fiscal_year: int
    certification_type: str
    certifier_name: str
    certifier_title: str
    icfr_effective: bool
    material_weaknesses_exist: bool
    material_weaknesses_disclosed: List[str]


@router.post("/processes", response_model=dict)
async def register_process(request: ProcessRegistrationRequest):
    """Register a SOX process"""
    process = await sox_service.register_process(
        process_name=request.process_name, process_description=request.process_description,
        business_unit=request.business_unit, process_owner=request.process_owner,
        financial_statement_areas=request.financial_statement_areas,
        assertions_addressed=request.assertions_addressed,
        materiality_threshold=request.materiality_threshold, risk_rating=request.risk_rating,
        documentation_location=request.documentation_location
    )
    return {"process_id": str(process.process_id), "process_code": process.process_code}


@router.get("/processes", response_model=List[dict])
async def list_processes(in_scope_only: bool = False, business_unit: Optional[str] = None):
    """List SOX processes"""
    if in_scope_only:
        processes = await sox_service.repository.find_in_scope_processes()
    elif business_unit:
        processes = await sox_service.repository.find_processes_by_business_unit(business_unit)
    else:
        processes = await sox_service.repository.find_all_processes()
    return [{"process_id": str(p.process_id), "process_code": p.process_code, "process_name": p.process_name, "in_scope": p.in_scope} for p in processes]


@router.get("/processes/{process_id}", response_model=dict)
async def get_process(process_id: UUID):
    """Get a specific SOX process"""
    process = await sox_service.repository.find_process_by_id(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return {
        "process_id": str(process.process_id),
        "process_code": process.process_code,
        "process_name": process.process_name,
        "business_unit": process.business_unit,
        "risk_rating": process.risk_rating,
        "in_scope": process.in_scope
    }


@router.post("/controls", response_model=dict)
async def create_control(request: ControlCreateRequest):
    """Create a SOX control"""
    control = await sox_service.create_control(
        process_id=request.process_id, control_name=request.control_name,
        control_description=request.control_description, control_objective=request.control_objective,
        assertions=request.assertions, control_type=request.control_type,
        control_nature=request.control_nature, control_frequency=request.control_frequency,
        control_owner=request.control_owner, performer=request.performer,
        evidence_type=request.evidence_type, evidence_retention=request.evidence_retention,
        key_control=request.key_control
    )
    return {"control_id": str(control.control_id), "control_code": control.control_code}


@router.get("/controls", response_model=List[dict])
async def list_controls(
    key_controls_only: bool = False,
    process_id: Optional[UUID] = None,
    active_only: bool = True
):
    """List SOX controls"""
    if key_controls_only:
        controls = await sox_service.repository.find_key_controls()
    elif process_id:
        controls = await sox_service.repository.find_controls_by_process(process_id)
    elif active_only:
        controls = await sox_service.repository.find_active_controls()
    else:
        controls = await sox_service.repository.find_all_controls()
    return [{"control_id": str(c.control_id), "control_code": c.control_code, "control_name": c.control_name, "key_control": c.key_control} for c in controls]


@router.get("/controls/{control_id}", response_model=dict)
async def get_control(control_id: UUID):
    """Get a specific SOX control"""
    control = await sox_service.repository.find_control_by_id(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return {
        "control_id": str(control.control_id),
        "control_code": control.control_code,
        "control_name": control.control_name,
        "control_objective": control.control_objective.value,
        "control_type": control.control_type,
        "key_control": control.key_control
    }


@router.post("/test-plans", response_model=dict)
async def create_test_plan(request: TestPlanCreateRequest):
    """Create a SOX test plan"""
    plan = await sox_service.create_test_plan(
        fiscal_year=request.fiscal_year, quarter=request.quarter, control_id=request.control_id,
        test_type=request.test_type, planned_test_date=request.planned_test_date,
        sample_size=request.sample_size, selection_method=request.selection_method,
        test_procedure=request.test_procedure, assigned_tester=request.assigned_tester
    )
    return {"plan_id": str(plan.plan_id), "fiscal_year": plan.fiscal_year, "quarter": plan.quarter}


@router.get("/test-plans", response_model=List[dict])
async def list_test_plans(fiscal_year: Optional[int] = None, pending_only: bool = False):
    """List SOX test plans"""
    if fiscal_year:
        plans = await sox_service.repository.find_test_plans_by_fiscal_year(fiscal_year)
    elif pending_only:
        plans = await sox_service.repository.find_pending_test_plans()
    else:
        plans = await sox_service.repository.find_all_test_plans()
    return [{"plan_id": str(p.plan_id), "fiscal_year": p.fiscal_year, "quarter": p.quarter, "status": p.status} for p in plans]


@router.post("/test-results", response_model=dict)
async def record_test_result(request: TestResultRequest):
    """Record a SOX test result"""
    result = await sox_service.record_test_result(
        plan_id=request.plan_id, control_id=request.control_id, tester=request.tester,
        population_size=request.population_size, sample_size=request.sample_size,
        items_tested=request.items_tested, exceptions_found=request.exceptions_found,
        test_evidence=request.test_evidence
    )
    return {
        "result_id": str(result.result_id),
        "overall_conclusion": result.overall_conclusion,
        "exception_rate": float(result.exception_rate)
    }


@router.get("/test-results", response_model=List[dict])
async def list_test_results(control_id: Optional[UUID] = None, ineffective_only: bool = False):
    """List SOX test results"""
    if control_id:
        results = await sox_service.repository.find_test_results_by_control(control_id)
    elif ineffective_only:
        results = await sox_service.repository.find_ineffective_test_results()
    else:
        results = await sox_service.repository.find_all_test_results()
    return [{"result_id": str(r.result_id), "control_id": str(r.control_id), "overall_conclusion": r.overall_conclusion} for r in results]


@router.get("/deficiencies", response_model=List[dict])
async def list_deficiencies(
    open_only: bool = False,
    material_weaknesses: bool = False,
    significant_only: bool = False
):
    """List SOX deficiencies"""
    if material_weaknesses:
        deficiencies = await sox_service.repository.find_material_weaknesses()
    elif significant_only:
        deficiencies = await sox_service.repository.find_significant_deficiencies()
    elif open_only:
        deficiencies = await sox_service.repository.find_open_deficiencies()
    else:
        deficiencies = await sox_service.repository.find_all_deficiencies()
    return [{"deficiency_id": str(d.deficiency_id), "deficiency_reference": d.deficiency_reference, "deficiency_type": d.deficiency_type.value, "status": d.status} for d in deficiencies]


@router.get("/deficiencies/{deficiency_id}", response_model=dict)
async def get_deficiency(deficiency_id: UUID):
    """Get a specific deficiency"""
    deficiency = await sox_service.repository.find_deficiency_by_id(deficiency_id)
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency not found")
    return {
        "deficiency_id": str(deficiency.deficiency_id),
        "deficiency_reference": deficiency.deficiency_reference,
        "deficiency_type": deficiency.deficiency_type.value,
        "description": deficiency.deficiency_description,
        "remediation_plan": deficiency.remediation_plan,
        "status": deficiency.status
    }


@router.post("/deficiencies/{deficiency_id}/close", response_model=dict)
async def close_deficiency(deficiency_id: UUID, closed_by: str = Query(...)):
    """Close a deficiency"""
    deficiency = await sox_service.close_deficiency(deficiency_id, closed_by)
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency not found")
    return {"deficiency_id": str(deficiency.deficiency_id), "status": deficiency.status}


@router.post("/certifications", response_model=dict)
async def create_certification(request: CertificationRequest):
    """Create a management certification"""
    certification = await sox_service.create_certification(
        fiscal_year=request.fiscal_year, certification_type=request.certification_type,
        certifier_name=request.certifier_name, certifier_title=request.certifier_title,
        icfr_effective=request.icfr_effective, material_weaknesses_exist=request.material_weaknesses_exist,
        material_weaknesses_disclosed=request.material_weaknesses_disclosed
    )
    return {"certification_id": str(certification.certification_id), "certification_type": certification.certification_type}


@router.get("/certifications", response_model=List[dict])
async def list_certifications(fiscal_year: Optional[int] = None):
    """List management certifications"""
    if fiscal_year:
        certifications = await sox_service.repository.find_certifications_by_fiscal_year(fiscal_year)
    else:
        certifications = await sox_service.repository.find_all_certifications()
    return [{"certification_id": str(c.certification_id), "fiscal_year": c.fiscal_year, "certification_type": c.certification_type} for c in certifications]


@router.post("/audit-committee-reports", response_model=dict)
async def generate_audit_committee_report(
    fiscal_year: int = Query(...),
    quarter: int = Query(...),
    presented_by: str = Query(...)
):
    """Generate an audit committee report"""
    report = await sox_service.generate_audit_committee_report(
        fiscal_year=fiscal_year, quarter=quarter, presented_by=presented_by
    )
    return {
        "report_id": str(report.audit_committee_id),
        "controls_tested": report.controls_tested,
        "controls_effective": report.controls_effective,
        "icfr_assessment": report.icfr_assessment
    }


@router.post("/reports/generate", response_model=dict)
async def generate_sox_report(fiscal_year: int = Query(...), generated_by: str = Query(...)):
    """Generate a SOX compliance report"""
    report = await sox_service.generate_report(fiscal_year=fiscal_year, generated_by=generated_by)
    return {
        "report_id": str(report.report_id),
        "report_date": str(report.report_date),
        "test_pass_rate": float(report.test_pass_rate)
    }


@router.get("/statistics", response_model=dict)
async def get_sox_statistics():
    """Get SOX compliance statistics"""
    return await sox_service.get_statistics()
