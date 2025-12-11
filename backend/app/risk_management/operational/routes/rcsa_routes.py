"""RCSA Routes - API endpoints for Risk Control Self-Assessment"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from ..models.rcsa_models import (
    RCSAAssessment, RCSARisk, RCSAControl, RCSAActionItem, RiskHeatmap, RCSAReport,
    RiskCategory, RiskLikelihood, RiskImpact, ControlEffectiveness, AssessmentStatus
)
from ..services.rcsa_service import rcsa_service

router = APIRouter(prefix="/rcsa", tags=["RCSA"])


class CreateAssessmentRequest(BaseModel):
    assessment_name: str
    business_unit: str
    process_name: str
    process_owner: str
    due_date: date
    assessor: str


class UpdateStatusRequest(BaseModel):
    new_status: AssessmentStatus
    reviewer: Optional[str] = None
    approver: Optional[str] = None


class AddRiskRequest(BaseModel):
    risk_name: str
    risk_description: str
    risk_category: RiskCategory
    risk_owner: str
    inherent_likelihood: RiskLikelihood
    inherent_impact: RiskImpact
    residual_likelihood: RiskLikelihood
    residual_impact: RiskImpact
    risk_appetite: str


class AddControlRequest(BaseModel):
    control_name: str
    control_description: str
    control_type: str
    control_nature: str
    control_owner: str
    frequency: str
    design_effectiveness: ControlEffectiveness
    operating_effectiveness: ControlEffectiveness
    risks_mitigated: Optional[List[UUID]] = None


class AddActionRequest(BaseModel):
    action_type: str
    action_description: str
    assigned_to: str
    due_date: date
    priority: str
    risk_id: Optional[UUID] = None
    control_id: Optional[UUID] = None


@router.post("/assessments", response_model=RCSAAssessment)
async def create_assessment(request: CreateAssessmentRequest):
    """Create new RCSA assessment"""
    return await rcsa_service.create_assessment(
        assessment_name=request.assessment_name,
        business_unit=request.business_unit,
        process_name=request.process_name,
        process_owner=request.process_owner,
        due_date=request.due_date,
        assessor=request.assessor
    )


@router.get("/assessments/{assessment_id}", response_model=RCSAAssessment)
async def get_assessment(assessment_id: UUID):
    """Get assessment by ID"""
    assessment = await rcsa_service.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.get("/assessments", response_model=List[RCSAAssessment])
async def list_assessments(
    status: Optional[AssessmentStatus] = Query(None),
    business_unit: Optional[str] = Query(None)
):
    """List RCSA assessments"""
    return await rcsa_service.list_assessments(status, business_unit)


@router.put("/assessments/{assessment_id}/status", response_model=RCSAAssessment)
async def update_status(assessment_id: UUID, request: UpdateStatusRequest):
    """Update assessment status"""
    assessment = await rcsa_service.update_assessment_status(
        assessment_id, request.new_status, request.reviewer, request.approver
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/assessments/{assessment_id}/risks", response_model=RCSARisk)
async def add_risk(assessment_id: UUID, request: AddRiskRequest):
    """Add risk to assessment"""
    return await rcsa_service.add_risk(
        assessment_id=assessment_id,
        risk_name=request.risk_name,
        risk_description=request.risk_description,
        risk_category=request.risk_category,
        risk_owner=request.risk_owner,
        inherent_likelihood=request.inherent_likelihood,
        inherent_impact=request.inherent_impact,
        residual_likelihood=request.residual_likelihood,
        residual_impact=request.residual_impact,
        risk_appetite=request.risk_appetite
    )


@router.get("/assessments/{assessment_id}/risks", response_model=List[RCSARisk])
async def get_risks(assessment_id: UUID):
    """Get risks for assessment"""
    return await rcsa_service.get_assessment_risks(assessment_id)


@router.post("/assessments/{assessment_id}/controls", response_model=RCSAControl)
async def add_control(assessment_id: UUID, request: AddControlRequest):
    """Add control to assessment"""
    return await rcsa_service.add_control(
        assessment_id=assessment_id,
        control_name=request.control_name,
        control_description=request.control_description,
        control_type=request.control_type,
        control_nature=request.control_nature,
        control_owner=request.control_owner,
        frequency=request.frequency,
        design_effectiveness=request.design_effectiveness,
        operating_effectiveness=request.operating_effectiveness,
        risks_mitigated=request.risks_mitigated
    )


@router.get("/assessments/{assessment_id}/controls", response_model=List[RCSAControl])
async def get_controls(assessment_id: UUID):
    """Get controls for assessment"""
    return await rcsa_service.get_assessment_controls(assessment_id)


@router.post("/assessments/{assessment_id}/actions", response_model=RCSAActionItem)
async def add_action(assessment_id: UUID, request: AddActionRequest):
    """Add action item to assessment"""
    return await rcsa_service.add_action_item(
        assessment_id=assessment_id,
        action_type=request.action_type,
        action_description=request.action_description,
        assigned_to=request.assigned_to,
        due_date=request.due_date,
        priority=request.priority,
        risk_id=request.risk_id,
        control_id=request.control_id
    )


@router.put("/actions/{action_id}/complete")
async def complete_action(action_id: UUID, verified_by: str):
    """Complete action item"""
    action = await rcsa_service.complete_action_item(action_id, verified_by)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.get("/assessments/{assessment_id}/actions", response_model=List[RCSAActionItem])
async def get_actions(assessment_id: UUID):
    """Get action items for assessment"""
    return await rcsa_service.get_assessment_actions(assessment_id)


@router.post("/heatmap", response_model=RiskHeatmap)
async def generate_heatmap(
    assessment_id: Optional[UUID] = None,
    business_unit: Optional[str] = None,
    heatmap_type: str = "residual"
):
    """Generate risk heatmap"""
    return await rcsa_service.generate_heatmap(assessment_id, business_unit, heatmap_type)


@router.post("/reports", response_model=RCSAReport)
async def generate_report(
    report_type: str,
    period: str,
    business_unit: Optional[str] = None,
    generated_by: str = "system"
):
    """Generate RCSA report"""
    return await rcsa_service.generate_report(report_type, period, business_unit, generated_by)


@router.get("/statistics")
async def get_statistics():
    """Get RCSA statistics"""
    return await rcsa_service.get_statistics()
