"""Data Validation Service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.data_validation_models import (
    ValidationRule, ValidationExecution, ValidationResult, ValidationError,
    ValidationSchedule, ValidationReport, RealTimeValidation, ValidationType
)
from ..repositories.data_validation_repository import data_validation_repository


class DataValidationService:
    def __init__(self):
        self.repository = data_validation_repository
        self._rule_counter = 0
        self._error_counter = 0

    async def create_rule(
        self, rule_name: str, rule_description: str, validation_type: ValidationType,
        target_table: str, validation_expression: str, error_message: str,
        owner: str, target_columns: List[str] = None, severity: str = "error",
        is_blocking: bool = False
    ) -> ValidationRule:
        self._rule_counter += 1
        rule = ValidationRule(
            rule_code=f"VR-{self._rule_counter:05d}", rule_name=rule_name,
            rule_description=rule_description, validation_type=validation_type,
            target_table=target_table, target_columns=target_columns or [],
            validation_expression=validation_expression, error_message=error_message,
            severity=severity, is_blocking=is_blocking, owner=owner
        )
        await self.repository.save_rule(rule)
        return rule

    async def start_execution(
        self, execution_name: str, execution_type: str, target_dataset: str,
        rules: List[UUID], triggered_by: str
    ) -> ValidationExecution:
        execution = ValidationExecution(
            execution_name=execution_name, execution_type=execution_type,
            target_dataset=target_dataset, rules_executed=rules,
            triggered_by=triggered_by
        )
        await self.repository.save_execution(execution)
        return execution

    async def record_result(
        self, execution_id: UUID, rule_id: UUID, rule_name: str,
        validation_type: str, records_evaluated: int, records_passed: int,
        error_samples: List[Dict[str, Any]] = None, execution_time_ms: int = 0
    ) -> ValidationResult:
        records_failed = records_evaluated - records_passed
        pass_percentage = Decimal(str(records_passed / records_evaluated * 100)) if records_evaluated > 0 else Decimal("100")
        status = "passed" if records_failed == 0 else "failed"

        result = ValidationResult(
            execution_id=execution_id, rule_id=rule_id, rule_name=rule_name,
            validation_type=validation_type, records_evaluated=records_evaluated,
            records_passed=records_passed, records_failed=records_failed,
            pass_percentage=pass_percentage, status=status,
            error_samples=error_samples or [], execution_time_ms=execution_time_ms
        )
        await self.repository.save_result(result)
        return result

    async def complete_execution(
        self, execution_id: UUID, total_records: int, valid_records: int, error_count: int
    ) -> Optional[ValidationExecution]:
        execution = await self.repository.find_execution_by_id(execution_id)
        if execution:
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.total_records = total_records
            execution.valid_records = valid_records
            execution.invalid_records = total_records - valid_records
            execution.error_count = error_count
        return execution

    async def record_error(
        self, result_id: UUID, rule_id: UUID, record_identifier: str,
        error_type: str, error_message: str, field_name: str = "",
        invalid_value: str = "", expected_value: str = ""
    ) -> ValidationError:
        self._error_counter += 1
        error = ValidationError(
            result_id=result_id, rule_id=rule_id, record_identifier=record_identifier,
            error_type=error_type, error_message=error_message, field_name=field_name,
            invalid_value=invalid_value, expected_value=expected_value
        )
        await self.repository.save_error(error)
        return error

    async def create_schedule(
        self, schedule_name: str, target_dataset: str, rules: List[UUID],
        cron_expression: str, created_by: str, notification_emails: List[str] = None
    ) -> ValidationSchedule:
        schedule = ValidationSchedule(
            schedule_name=schedule_name, target_dataset=target_dataset,
            rules=rules, cron_expression=cron_expression,
            notification_emails=notification_emails or [], created_by=created_by
        )
        await self.repository.save_schedule(schedule)
        return schedule

    async def validate_realtime(
        self, stream_name: str, rule_id: UUID, record_id: str,
        is_valid: bool, error_details: str = None, action_taken: str = "accepted"
    ) -> RealTimeValidation:
        validation = RealTimeValidation(
            stream_name=stream_name, rule_id=rule_id, record_id=record_id,
            is_valid=is_valid, error_details=error_details, action_taken=action_taken
        )
        await self.repository.save_realtime_validation(validation)
        return validation

    async def generate_report(
        self, report_period: str, generated_by: str
    ) -> ValidationReport:
        executions = await self.repository.find_all_executions()
        results = await self.repository.find_all_results()

        total_validated = sum(e.total_records for e in executions if e.status == "completed")
        total_valid = sum(e.valid_records for e in executions if e.status == "completed")
        pass_rate = Decimal(str(total_valid / total_validated * 100)) if total_validated > 0 else Decimal("100")

        report = ValidationReport(
            report_date=date.today(), report_period=report_period,
            datasets_validated=len(set(e.target_dataset for e in executions)),
            rules_executed=len(results), total_records_validated=total_validated,
            overall_pass_rate=pass_rate, generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


data_validation_service = DataValidationService()
