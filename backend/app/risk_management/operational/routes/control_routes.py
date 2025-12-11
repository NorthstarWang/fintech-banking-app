"""Control Routes - API endpoints for control management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.control_models import (
    Control, ControlTest, ControlException, ControlGap,
    ControlFramework, ControlMapping, ControlMetrics,
    ControlType, ControlNature, ControlCategory, ControlStatus
)
from ..services.control_service import control_service

router = APIRouter(prefix="/controls", tags=["Controls"])


class CreateControlRequest(BaseModel):
    control_name: str
    control_description: str
    control_objective: str
    control_type: ControlType
    control_nature: ControlNature
    control_category: ControlCategory
    business_unit: str
    process: str
    owner: str
    frequency: str
    evidence_type: str
    evidence_location: str
    key_control: bool = False
    sox_control: bool = False
    regulatory_control: bool = False


class RecordTestRequest(BaseModel):
    test_name: str
    test_type: str
    test_date: date
    test_period_start: date
    test_period_end: date
    tester: str
    sample_size: int
    population_size: int
    exceptions_found: int
    test_procedure: str
    findings: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class RecordExceptionRequest(BaseModel):
    test_id: UUID
    exception_date: date
    exception_description: str
    root_cause: str
    impact: str
    severity: str
    remediation_action: Optional[str] = None
    remediation_owner: Optional[str] = None
    remediation_due_date: Optional[date] = None


class RecordGapRequest(BaseModel):
    gap_type: str
    gap_description: str
    identified_by: str
    risk_exposure: str
    business_unit: str
    process: str
    severity: str
    remediation_plan: str
    remediation_owner: str
    target_remediation_date: date
    control_id: Optional[UUID] = None


class CreateFrameworkRequest(BaseModel):
    framework_name: str
    framework_version: str
    description: str
    issuing_body: str
    effective_date: date
    domains: List[str]
    total_controls: int


class MapControlRequest(BaseModel):
    control_id: UUID
    framework_id: UUID
    framework_control_id: str
    framework_control_name: str
    mapping_status: str


@router.post("/", response_model=Control)
async def create_control(request: CreateControlRequest):
    """Create new control"""
    return await control_service.create_control(
        control_name=request.control_name,
        control_description=request.control_description,
        control_objective=request.control_objective,
        control_type=request.control_type,
        control_nature=request.control_nature,
        control_category=request.control_category,
        business_unit=request.business_unit,
        process=request.process,
        owner=request.owner,
        frequency=request.frequency,
        evidence_type=request.evidence_type,
        evidence_location=request.evidence_location,
        key_control=request.key_control,
        sox_control=request.sox_control,
        regulatory_control=request.regulatory_control
    )


@router.get("/{control_id}", response_model=Control)
async def get_control(control_id: UUID):
    """Get control by ID"""
    control = await control_service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.get("/code/{control_code}", response_model=Control)
async def get_control_by_code(control_code: str):
    """Get control by code"""
    control = await control_service.get_control_by_code(control_code)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.get("/", response_model=List[Control])
async def list_controls(
    status: Optional[ControlStatus] = Query(None),
    control_type: Optional[ControlType] = Query(None),
    business_unit: Optional[str] = Query(None),
    key_control: Optional[bool] = Query(None),
    sox_control: Optional[bool] = Query(None)
):
    """List controls"""
    return await control_service.list_controls(
        status, control_type, business_unit, key_control, sox_control
    )


@router.put("/{control_id}/status", response_model=Control)
async def update_status(control_id: UUID, new_status: ControlStatus):
    """Update control status"""
    control = await control_service.update_control_status(control_id, new_status)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.post("/{control_id}/tests", response_model=ControlTest)
async def record_test(control_id: UUID, request: RecordTestRequest):
    """Record control test"""
    return await control_service.record_test(
        control_id=control_id,
        test_name=request.test_name,
        test_type=request.test_type,
        test_date=request.test_date,
        test_period_start=request.test_period_start,
        test_period_end=request.test_period_end,
        tester=request.tester,
        sample_size=request.sample_size,
        population_size=request.population_size,
        exceptions_found=request.exceptions_found,
        test_procedure=request.test_procedure,
        findings=request.findings,
        recommendations=request.recommendations
    )


@router.get("/{control_id}/tests", response_model=List[ControlTest])
async def get_tests(control_id: UUID):
    """Get control tests"""
    return await control_service.get_control_tests(control_id)


@router.post("/{control_id}/exceptions", response_model=ControlException)
async def record_exception(control_id: UUID, request: RecordExceptionRequest):
    """Record control exception"""
    return await control_service.record_exception(
        control_id=control_id,
        test_id=request.test_id,
        exception_date=request.exception_date,
        exception_description=request.exception_description,
        root_cause=request.root_cause,
        impact=request.impact,
        severity=request.severity,
        remediation_action=request.remediation_action,
        remediation_owner=request.remediation_owner,
        remediation_due_date=request.remediation_due_date
    )


@router.put("/exceptions/{exception_id}/close")
async def close_exception(exception_id: UUID, verified_by: str):
    """Close control exception"""
    exception = await control_service.close_exception(exception_id, verified_by)
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    return exception


@router.post("/gaps", response_model=ControlGap)
async def record_gap(request: RecordGapRequest):
    """Record control gap"""
    return await control_service.record_gap(
        gap_type=request.gap_type,
        gap_description=request.gap_description,
        identified_by=request.identified_by,
        risk_exposure=request.risk_exposure,
        business_unit=request.business_unit,
        process=request.process,
        severity=request.severity,
        remediation_plan=request.remediation_plan,
        remediation_owner=request.remediation_owner,
        target_remediation_date=request.target_remediation_date,
        control_id=request.control_id
    )


@router.put("/gaps/{gap_id}/close")
async def close_gap(gap_id: UUID, validated_by: str):
    """Close control gap"""
    gap = await control_service.close_gap(gap_id, validated_by)
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    return gap


@router.get("/gaps/open", response_model=List[ControlGap])
async def get_open_gaps(business_unit: Optional[str] = Query(None)):
    """Get open control gaps"""
    return await control_service.get_open_gaps(business_unit)


@router.post("/frameworks", response_model=ControlFramework)
async def create_framework(request: CreateFrameworkRequest):
    """Create control framework"""
    return await control_service.create_framework(
        framework_name=request.framework_name,
        framework_version=request.framework_version,
        description=request.description,
        issuing_body=request.issuing_body,
        effective_date=request.effective_date,
        domains=request.domains,
        total_controls=request.total_controls
    )


@router.post("/mappings", response_model=ControlMapping)
async def map_control(request: MapControlRequest):
    """Map control to framework"""
    return await control_service.map_control_to_framework(
        control_id=request.control_id,
        framework_id=request.framework_id,
        framework_control_id=request.framework_control_id,
        framework_control_name=request.framework_control_name,
        mapping_status=request.mapping_status
    )


@router.get("/metrics", response_model=ControlMetrics)
async def get_metrics(business_unit: Optional[str] = Query(None)):
    """Get control metrics"""
    return await control_service.generate_metrics(business_unit)


@router.get("/statistics")
async def get_statistics():
    """Get control statistics"""
    return await control_service.get_statistics()
