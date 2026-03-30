"""Business Continuity Routes - API endpoints for BCP/DR management"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.business_continuity_models import (
    BCPIncident,
    BCPMetrics,
    BCPStatus,
    BCPTest,
    BusinessContinuityPlan,
    BusinessProcess,
    CrisisTeamMember,
    CriticalityLevel,
    DisasterRecoveryPlan,
    DisasterType,
    RecoveryStrategy,
    TestType,
)
from ..services.business_continuity_service import business_continuity_service

router = APIRouter(prefix="/bcp", tags=["Business Continuity"])


class RegisterProcessRequest(BaseModel):
    process_name: str
    process_description: str
    business_unit: str
    process_owner: str
    criticality: CriticalityLevel
    rto_hours: int
    rpo_hours: int
    mtpd_hours: int
    minimum_staff: int
    normal_staff: int
    recovery_strategy: RecoveryStrategy
    financial_impact_per_hour: Decimal
    dependencies: list[str] | None = None
    systems_required: list[str] | None = None
    vendors_required: list[str] | None = None


class CreateBCPRequest(BaseModel):
    plan_name: str
    plan_version: str
    business_unit: str
    plan_owner: str
    scope: str
    objectives: list[str]
    assumptions: list[str]
    processes_covered: list[UUID]
    activation_criteria: list[str]
    deactivation_criteria: list[str]
    document_location: str


class CreateDRPRequest(BaseModel):
    plan_name: str
    plan_version: str
    system_name: str
    system_criticality: CriticalityLevel
    rto_hours: int
    rpo_hours: int
    recovery_site: str
    recovery_strategy: RecoveryStrategy
    backup_frequency: str
    backup_location: str
    backup_retention: str
    recovery_procedures: list[str]
    verification_steps: list[str]
    owner: str
    dependencies: list[str] | None = None


class ScheduleTestRequest(BaseModel):
    test_name: str
    test_type: TestType
    test_date: date
    scope: str
    objectives: list[str]
    scenarios_tested: list[str]
    test_coordinator: str
    participants: list[str]


class CompleteTestRequest(BaseModel):
    test_duration_hours: float
    test_result: str
    rto_achieved: int
    rpo_achieved: int
    findings: list[str]
    recommendations: list[str]
    lessons_learned: list[str]


class DeclareIncidentRequest(BaseModel):
    incident_name: str
    disaster_type: DisasterType
    declared_by: str
    affected_locations: list[str]
    affected_processes: list[UUID]
    impact_description: str
    plan_activated: UUID


class AddTeamMemberRequest(BaseModel):
    team_name: str
    role: str
    primary_contact: str
    primary_phone: str
    primary_email: str
    responsibilities: list[str]
    alternate_contact: str | None = None
    alternate_phone: str | None = None
    backup_person: str | None = None
    backup_phone: str | None = None


@router.post("/processes", response_model=BusinessProcess)
async def register_process(request: RegisterProcessRequest):
    """Register business process"""
    return await business_continuity_service.register_process(
        process_name=request.process_name,
        process_description=request.process_description,
        business_unit=request.business_unit,
        process_owner=request.process_owner,
        criticality=request.criticality,
        rto_hours=request.rto_hours,
        rpo_hours=request.rpo_hours,
        mtpd_hours=request.mtpd_hours,
        minimum_staff=request.minimum_staff,
        normal_staff=request.normal_staff,
        recovery_strategy=request.recovery_strategy,
        financial_impact_per_hour=request.financial_impact_per_hour,
        dependencies=request.dependencies,
        systems_required=request.systems_required,
        vendors_required=request.vendors_required
    )


@router.get("/processes/{process_id}", response_model=BusinessProcess)
async def get_process(process_id: UUID):
    """Get business process"""
    process = await business_continuity_service.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.get("/processes", response_model=list[BusinessProcess])
async def list_processes(
    criticality: CriticalityLevel | None = Query(None),
    business_unit: str | None = Query(None)
):
    """List business processes"""
    return await business_continuity_service.list_processes(criticality, business_unit)


@router.post("/plans", response_model=BusinessContinuityPlan)
async def create_bcp(request: CreateBCPRequest):
    """Create business continuity plan"""
    return await business_continuity_service.create_bcp(
        plan_name=request.plan_name,
        plan_version=request.plan_version,
        business_unit=request.business_unit,
        plan_owner=request.plan_owner,
        scope=request.scope,
        objectives=request.objectives,
        assumptions=request.assumptions,
        processes_covered=request.processes_covered,
        activation_criteria=request.activation_criteria,
        deactivation_criteria=request.deactivation_criteria,
        document_location=request.document_location
    )


@router.get("/plans/{plan_id}", response_model=BusinessContinuityPlan)
async def get_bcp(plan_id: UUID):
    """Get BCP by ID"""
    plan = await business_continuity_service.get_bcp(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/plans", response_model=list[BusinessContinuityPlan])
async def list_bcps(
    status: BCPStatus | None = Query(None),
    business_unit: str | None = Query(None)
):
    """List BCPs"""
    return await business_continuity_service.list_bcps(status, business_unit)


@router.put("/plans/{plan_id}/approve", response_model=BusinessContinuityPlan)
async def approve_bcp(plan_id: UUID, approved_by: str):
    """Approve BCP"""
    plan = await business_continuity_service.approve_bcp(plan_id, approved_by)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/dr-plans", response_model=DisasterRecoveryPlan)
async def create_drp(request: CreateDRPRequest):
    """Create disaster recovery plan"""
    return await business_continuity_service.create_drp(
        plan_name=request.plan_name,
        plan_version=request.plan_version,
        system_name=request.system_name,
        system_criticality=request.system_criticality,
        rto_hours=request.rto_hours,
        rpo_hours=request.rpo_hours,
        recovery_site=request.recovery_site,
        recovery_strategy=request.recovery_strategy,
        backup_frequency=request.backup_frequency,
        backup_location=request.backup_location,
        backup_retention=request.backup_retention,
        recovery_procedures=request.recovery_procedures,
        verification_steps=request.verification_steps,
        owner=request.owner,
        dependencies=request.dependencies
    )


@router.get("/dr-plans", response_model=list[DisasterRecoveryPlan])
async def list_drps(
    status: BCPStatus | None = Query(None),
    criticality: CriticalityLevel | None = Query(None)
):
    """List DRPs"""
    return await business_continuity_service.list_drps(status, criticality)


@router.post("/tests", response_model=BCPTest)
async def schedule_test(plan_id: UUID, request: ScheduleTestRequest):
    """Schedule BCP/DR test"""
    return await business_continuity_service.schedule_test(
        plan_id=plan_id,
        test_name=request.test_name,
        test_type=request.test_type,
        test_date=request.test_date,
        scope=request.scope,
        objectives=request.objectives,
        scenarios_tested=request.scenarios_tested,
        test_coordinator=request.test_coordinator,
        participants=request.participants
    )


@router.put("/tests/{test_id}/complete", response_model=BCPTest)
async def complete_test(test_id: UUID, request: CompleteTestRequest):
    """Complete BCP/DR test"""
    test = await business_continuity_service.complete_test(
        test_id=test_id,
        test_duration_hours=request.test_duration_hours,
        test_result=request.test_result,
        rto_achieved=request.rto_achieved,
        rpo_achieved=request.rpo_achieved,
        findings=request.findings,
        recommendations=request.recommendations,
        lessons_learned=request.lessons_learned
    )
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.get("/plans/{plan_id}/tests", response_model=list[BCPTest])
async def get_plan_tests(plan_id: UUID):
    """Get tests for plan"""
    return await business_continuity_service.get_plan_tests(plan_id)


@router.post("/incidents", response_model=BCPIncident)
async def declare_incident(request: DeclareIncidentRequest):
    """Declare BCP incident"""
    return await business_continuity_service.declare_incident(
        incident_name=request.incident_name,
        disaster_type=request.disaster_type,
        declared_by=request.declared_by,
        affected_locations=request.affected_locations,
        affected_processes=request.affected_processes,
        impact_description=request.impact_description,
        plan_activated=request.plan_activated
    )


@router.put("/incidents/{incident_id}/start-recovery", response_model=BCPIncident)
async def start_recovery(incident_id: UUID):
    """Start incident recovery"""
    incident = await business_continuity_service.start_recovery(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/incidents/{incident_id}/complete-recovery", response_model=BCPIncident)
async def complete_recovery(incident_id: UUID, lessons_learned: list[str]):
    """Complete incident recovery"""
    incident = await business_continuity_service.complete_recovery(incident_id, lessons_learned)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/incidents/{incident_id}/close", response_model=BCPIncident)
async def close_incident(incident_id: UUID, financial_impact: Decimal):
    """Close BCP incident"""
    incident = await business_continuity_service.close_incident(incident_id, financial_impact)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/incidents/active", response_model=list[BCPIncident])
async def get_active_incidents():
    """Get active incidents"""
    return await business_continuity_service.get_active_incidents()


@router.post("/teams/members", response_model=CrisisTeamMember)
async def add_team_member(request: AddTeamMemberRequest):
    """Add crisis team member"""
    return await business_continuity_service.add_crisis_team_member(
        team_name=request.team_name,
        role=request.role,
        primary_contact=request.primary_contact,
        primary_phone=request.primary_phone,
        primary_email=request.primary_email,
        responsibilities=request.responsibilities,
        alternate_contact=request.alternate_contact,
        alternate_phone=request.alternate_phone,
        backup_person=request.backup_person,
        backup_phone=request.backup_phone
    )


@router.get("/teams/{team_name}", response_model=list[CrisisTeamMember])
async def get_team(team_name: str):
    """Get crisis team"""
    return await business_continuity_service.get_crisis_team(team_name)


@router.get("/metrics", response_model=BCPMetrics)
async def get_metrics(business_unit: str | None = Query(None)):
    """Get BCP metrics"""
    return await business_continuity_service.generate_metrics(business_unit)


@router.get("/statistics")
async def get_statistics():
    """Get BCP statistics"""
    return await business_continuity_service.get_statistics()
