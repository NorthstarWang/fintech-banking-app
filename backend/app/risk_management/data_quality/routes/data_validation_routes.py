"""Data Validation Routes"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.data_validation_models import ValidationType
from ..services.data_validation_service import data_validation_service

router = APIRouter(prefix="/data-validation", tags=["Data Validation"])


class CreateRuleRequest(BaseModel):
    rule_name: str
    rule_description: str
    validation_type: ValidationType
    target_table: str
    validation_expression: str
    error_message: str
    owner: str
    target_columns: List[str] = []
    severity: str = "error"
    is_blocking: bool = False


class StartExecutionRequest(BaseModel):
    execution_name: str
    execution_type: str
    target_dataset: str
    rules: List[UUID]
    triggered_by: str


class RecordResultRequest(BaseModel):
    execution_id: UUID
    rule_id: UUID
    rule_name: str
    validation_type: str
    records_evaluated: int
    records_passed: int
    error_samples: List[Dict[str, Any]] = []
    execution_time_ms: int = 0


class RecordErrorRequest(BaseModel):
    result_id: UUID
    rule_id: UUID
    record_identifier: str
    error_type: str
    error_message: str
    field_name: str = ""
    invalid_value: str = ""
    expected_value: str = ""


class CreateScheduleRequest(BaseModel):
    schedule_name: str
    target_dataset: str
    rules: List[UUID]
    cron_expression: str
    created_by: str
    notification_emails: List[str] = []


class ValidateRealtimeRequest(BaseModel):
    stream_name: str
    rule_id: UUID
    record_id: str
    is_valid: bool
    error_details: Optional[str] = None
    action_taken: str = "accepted"


@router.post("/rules")
async def create_rule(request: CreateRuleRequest):
    rule = await data_validation_service.create_rule(
        rule_name=request.rule_name,
        rule_description=request.rule_description,
        validation_type=request.validation_type,
        target_table=request.target_table,
        validation_expression=request.validation_expression,
        error_message=request.error_message,
        owner=request.owner,
        target_columns=request.target_columns,
        severity=request.severity,
        is_blocking=request.is_blocking,
    )
    return {"status": "created", "rule_id": str(rule.rule_id), "rule_code": rule.rule_code}


@router.get("/rules")
async def get_all_rules():
    rules = await data_validation_service.repository.find_all_rules()
    return {"rules": [{"rule_id": str(r.rule_id), "name": r.rule_name, "code": r.rule_code} for r in rules]}


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: UUID):
    rule = await data_validation_service.repository.find_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.get("/rules/table/{target_table}")
async def get_rules_by_table(target_table: str):
    rules = await data_validation_service.repository.find_rules_by_table(target_table)
    return {"rules": [{"rule_id": str(r.rule_id), "name": r.rule_name} for r in rules]}


@router.get("/rules/active")
async def get_active_rules():
    rules = await data_validation_service.repository.find_active_rules()
    return {"rules": [{"rule_id": str(r.rule_id), "name": r.rule_name, "table": r.target_table} for r in rules]}


@router.get("/rules/blocking")
async def get_blocking_rules():
    rules = await data_validation_service.repository.find_blocking_rules()
    return {"rules": [{"rule_id": str(r.rule_id), "name": r.rule_name} for r in rules]}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: UUID):
    deleted = await data_validation_service.repository.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted"}


@router.post("/executions")
async def start_execution(request: StartExecutionRequest):
    execution = await data_validation_service.start_execution(
        execution_name=request.execution_name,
        execution_type=request.execution_type,
        target_dataset=request.target_dataset,
        rules=request.rules,
        triggered_by=request.triggered_by,
    )
    return {"status": "started", "execution_id": str(execution.execution_id)}


@router.post("/executions/{execution_id}/complete")
async def complete_execution(execution_id: UUID, total_records: int, valid_records: int, error_count: int):
    execution = await data_validation_service.complete_execution(
        execution_id=execution_id,
        total_records=total_records,
        valid_records=valid_records,
        error_count=error_count,
    )
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"status": "completed", "execution_id": str(execution.execution_id)}


@router.get("/executions")
async def get_all_executions():
    executions = await data_validation_service.repository.find_all_executions()
    return {"executions": [{"id": str(e.execution_id), "name": e.execution_name, "status": e.status} for e in executions]}


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: UUID):
    execution = await data_validation_service.repository.find_execution_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/executions/running")
async def get_running_executions():
    executions = await data_validation_service.repository.find_running_executions()
    return {"executions": [{"id": str(e.execution_id), "name": e.execution_name} for e in executions]}


@router.post("/results")
async def record_result(request: RecordResultRequest):
    result = await data_validation_service.record_result(
        execution_id=request.execution_id,
        rule_id=request.rule_id,
        rule_name=request.rule_name,
        validation_type=request.validation_type,
        records_evaluated=request.records_evaluated,
        records_passed=request.records_passed,
        error_samples=request.error_samples,
        execution_time_ms=request.execution_time_ms,
    )
    return {"status": "recorded", "result_id": str(result.result_id), "result_status": result.status}


@router.get("/results")
async def get_all_results():
    results = await data_validation_service.repository.find_all_results()
    return {"results": [{"result_id": str(r.result_id), "rule": r.rule_name, "status": r.status} for r in results]}


@router.get("/results/execution/{execution_id}")
async def get_results_by_execution(execution_id: UUID):
    results = await data_validation_service.repository.find_results_by_execution(execution_id)
    return {"results": [{"result_id": str(r.result_id), "rule": r.rule_name, "status": r.status} for r in results]}


@router.get("/results/failed")
async def get_failed_results():
    results = await data_validation_service.repository.find_failed_results()
    return {"results": [{"result_id": str(r.result_id), "rule": r.rule_name, "failed": r.records_failed} for r in results]}


@router.post("/errors")
async def record_error(request: RecordErrorRequest):
    error = await data_validation_service.record_error(
        result_id=request.result_id,
        rule_id=request.rule_id,
        record_identifier=request.record_identifier,
        error_type=request.error_type,
        error_message=request.error_message,
        field_name=request.field_name,
        invalid_value=request.invalid_value,
        expected_value=request.expected_value,
    )
    return {"status": "recorded", "error_id": str(error.error_id)}


@router.get("/errors")
async def get_all_errors():
    errors = await data_validation_service.repository.find_all_errors()
    return {"errors": [{"error_id": str(e.error_id), "type": e.error_type, "message": e.error_message} for e in errors]}


@router.get("/errors/result/{result_id}")
async def get_errors_by_result(result_id: UUID):
    errors = await data_validation_service.repository.find_errors_by_result(result_id)
    return {"errors": [{"error_id": str(e.error_id), "type": e.error_type, "record": e.record_identifier} for e in errors]}


@router.post("/schedules")
async def create_schedule(request: CreateScheduleRequest):
    schedule = await data_validation_service.create_schedule(
        schedule_name=request.schedule_name,
        target_dataset=request.target_dataset,
        rules=request.rules,
        cron_expression=request.cron_expression,
        created_by=request.created_by,
        notification_emails=request.notification_emails,
    )
    return {"status": "created", "schedule_id": str(schedule.schedule_id)}


@router.get("/schedules")
async def get_all_schedules():
    schedules = await data_validation_service.repository.find_all_schedules()
    return {"schedules": [{"id": str(s.schedule_id), "name": s.schedule_name, "cron": s.cron_expression} for s in schedules]}


@router.get("/schedules/active")
async def get_active_schedules():
    schedules = await data_validation_service.repository.find_active_schedules()
    return {"schedules": [{"id": str(s.schedule_id), "name": s.schedule_name} for s in schedules]}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: UUID):
    deleted = await data_validation_service.repository.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}


@router.post("/reports")
async def generate_report(report_period: str, generated_by: str):
    report = await data_validation_service.generate_report(
        report_period=report_period,
        generated_by=generated_by,
    )
    return {"status": "generated", "report_id": str(report.report_id), "pass_rate": float(report.overall_pass_rate)}


@router.get("/reports")
async def get_all_reports():
    reports = await data_validation_service.repository.find_all_reports()
    return {"reports": [{"report_id": str(r.report_id), "period": r.report_period, "pass_rate": float(r.overall_pass_rate)} for r in reports]}


@router.post("/realtime")
async def validate_realtime(request: ValidateRealtimeRequest):
    validation = await data_validation_service.validate_realtime(
        stream_name=request.stream_name,
        rule_id=request.rule_id,
        record_id=request.record_id,
        is_valid=request.is_valid,
        error_details=request.error_details,
        action_taken=request.action_taken,
    )
    return {"status": "validated", "validation_id": str(validation.validation_id), "is_valid": validation.is_valid}


@router.get("/realtime")
async def get_all_realtime_validations():
    validations = await data_validation_service.repository.find_all_realtime_validations()
    return {"validations": [{"id": str(v.validation_id), "stream": v.stream_name, "valid": v.is_valid} for v in validations]}


@router.get("/realtime/stream/{stream_name}")
async def get_realtime_by_stream(stream_name: str):
    validations = await data_validation_service.repository.find_realtime_validations_by_stream(stream_name)
    return {"validations": [{"id": str(v.validation_id), "record": v.record_id, "valid": v.is_valid} for v in validations]}


@router.get("/realtime/failed")
async def get_failed_realtime_validations():
    validations = await data_validation_service.repository.find_failed_realtime_validations()
    return {"validations": [{"id": str(v.validation_id), "stream": v.stream_name, "error": v.error_details} for v in validations]}


@router.get("/statistics")
async def get_statistics():
    return await data_validation_service.get_statistics()
