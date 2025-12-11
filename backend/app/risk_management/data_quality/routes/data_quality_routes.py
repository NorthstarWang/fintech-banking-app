"""Data Quality Routes"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.data_quality_service import data_quality_service

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


class CreateRuleRequest(BaseModel):
    rule_name: str
    rule_description: str
    dimension: str
    target_dataset: str
    target_columns: List[str]
    rule_expression: str
    error_message: str
    owner: str
    severity: str = "error"
    threshold: Decimal = Decimal("100")


class RunCheckRequest(BaseModel):
    rule_id: UUID
    dataset_name: str
    triggered_by: str


class RecordScoreRequest(BaseModel):
    dataset_name: str
    dimension: str
    score: Decimal
    records_total: int
    records_passed: int
    measured_by: str


class CreateIssueRequest(BaseModel):
    issue_title: str
    issue_description: str
    dataset_name: str
    dimension: str
    severity: str
    reported_by: str
    assigned_to: str = ""


class CreateThresholdRequest(BaseModel):
    dataset_name: str
    dimension: str
    threshold_value: Decimal
    comparison_operator: str
    action_on_breach: str
    notification_emails: List[str]
    created_by: str


class CreateDimensionRequest(BaseModel):
    dimension_name: str
    dimension_code: str
    description: str
    weight: Decimal
    owner: str


class CreateSLARequest(BaseModel):
    sla_name: str
    dataset_name: str
    dimension: str
    target_value: Decimal
    measurement_frequency: str
    owner: str
    stakeholders: List[str]


@router.post("/rules")
async def create_rule(request: CreateRuleRequest):
    rule = await data_quality_service.create_rule(
        rule_name=request.rule_name,
        rule_description=request.rule_description,
        dimension=request.dimension,
        target_dataset=request.target_dataset,
        target_columns=request.target_columns,
        rule_expression=request.rule_expression,
        error_message=request.error_message,
        owner=request.owner,
        severity=request.severity,
        threshold=request.threshold,
    )
    return {"status": "created", "rule_id": str(rule.rule_id)}


@router.get("/rules")
async def get_all_rules():
    rules = await data_quality_service.repository.find_all_rules()
    return {"rules": [{"rule_id": str(r.rule_id), "rule_name": r.rule_name, "dimension": r.dimension} for r in rules]}


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: UUID):
    rule = await data_quality_service.repository.find_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/checks")
async def run_check(request: RunCheckRequest):
    check = await data_quality_service.run_check(
        rule_id=request.rule_id,
        dataset_name=request.dataset_name,
        triggered_by=request.triggered_by,
    )
    return {"status": "started", "check_id": str(check.check_id)}


@router.post("/checks/{check_id}/complete")
async def complete_check(
    check_id: UUID,
    records_checked: int,
    records_passed: int,
    error_details: Optional[List[Dict[str, Any]]] = None,
):
    check = await data_quality_service.complete_check(
        check_id=check_id,
        records_checked=records_checked,
        records_passed=records_passed,
        error_details=error_details,
    )
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    return {"status": "completed", "check_id": str(check.check_id), "result": check.status}


@router.get("/checks")
async def get_all_checks():
    checks = await data_quality_service.repository.find_all_checks()
    return {"checks": [{"check_id": str(c.check_id), "status": c.status} for c in checks]}


@router.post("/scores")
async def record_score(request: RecordScoreRequest):
    score = await data_quality_service.record_score(
        dataset_name=request.dataset_name,
        dimension=request.dimension,
        score=request.score,
        records_total=request.records_total,
        records_passed=request.records_passed,
        measured_by=request.measured_by,
    )
    return {"status": "recorded", "score_id": str(score.score_id)}


@router.get("/scores")
async def get_all_scores():
    scores = await data_quality_service.repository.find_all_scores()
    return {"scores": [{"score_id": str(s.score_id), "dataset": s.dataset_name, "score": float(s.score)} for s in scores]}


@router.post("/issues")
async def create_issue(request: CreateIssueRequest):
    issue = await data_quality_service.create_issue(
        issue_title=request.issue_title,
        issue_description=request.issue_description,
        dataset_name=request.dataset_name,
        dimension=request.dimension,
        severity=request.severity,
        reported_by=request.reported_by,
        assigned_to=request.assigned_to,
    )
    return {"status": "created", "issue_id": str(issue.issue_id)}


@router.post("/issues/{issue_id}/resolve")
async def resolve_issue(issue_id: UUID, resolution: str, resolved_by: str):
    issue = await data_quality_service.resolve_issue(
        issue_id=issue_id,
        resolution=resolution,
        resolved_by=resolved_by,
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"status": "resolved", "issue_id": str(issue.issue_id)}


@router.get("/issues")
async def get_all_issues():
    issues = await data_quality_service.repository.find_all_issues()
    return {"issues": [{"issue_id": str(i.issue_id), "title": i.issue_title, "status": i.status} for i in issues]}


@router.post("/reports")
async def generate_report(report_period: str, generated_by: str):
    report = await data_quality_service.generate_report(
        report_period=report_period,
        generated_by=generated_by,
    )
    return {"status": "generated", "report_id": str(report.report_id)}


@router.get("/reports")
async def get_all_reports():
    reports = await data_quality_service.repository.find_all_reports()
    return {"reports": [{"report_id": str(r.report_id), "period": r.report_period} for r in reports]}


@router.post("/thresholds")
async def create_threshold(request: CreateThresholdRequest):
    threshold = await data_quality_service.create_threshold(
        dataset_name=request.dataset_name,
        dimension=request.dimension,
        threshold_value=request.threshold_value,
        comparison_operator=request.comparison_operator,
        action_on_breach=request.action_on_breach,
        notification_emails=request.notification_emails,
        created_by=request.created_by,
    )
    return {"status": "created", "threshold_id": str(threshold.threshold_id)}


@router.get("/thresholds")
async def get_all_thresholds():
    thresholds = await data_quality_service.repository.find_all_thresholds()
    return {"thresholds": [{"threshold_id": str(t.threshold_id), "dataset": t.dataset_name} for t in thresholds]}


@router.post("/dimensions")
async def create_dimension(request: CreateDimensionRequest):
    dimension = await data_quality_service.create_dimension(
        dimension_name=request.dimension_name,
        dimension_code=request.dimension_code,
        description=request.description,
        weight=request.weight,
        owner=request.owner,
    )
    return {"status": "created", "dimension_id": str(dimension.dimension_id)}


@router.get("/dimensions")
async def get_all_dimensions():
    dimensions = await data_quality_service.repository.find_all_dimensions()
    return {"dimensions": [{"dimension_id": str(d.dimension_id), "name": d.dimension_name} for d in dimensions]}


@router.post("/slas")
async def create_sla(request: CreateSLARequest):
    sla = await data_quality_service.create_sla(
        sla_name=request.sla_name,
        dataset_name=request.dataset_name,
        dimension=request.dimension,
        target_value=request.target_value,
        measurement_frequency=request.measurement_frequency,
        owner=request.owner,
        stakeholders=request.stakeholders,
    )
    return {"status": "created", "sla_id": str(sla.sla_id)}


@router.get("/slas")
async def get_all_slas():
    slas = await data_quality_service.repository.find_all_slas()
    return {"slas": [{"sla_id": str(s.sla_id), "name": s.sla_name} for s in slas]}


@router.get("/statistics")
async def get_statistics():
    return await data_quality_service.get_statistics()
