"""Data Validation Repository"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.data_validation_models import (
    ValidationRule, ValidationExecution, ValidationResult, ValidationError,
    ValidationSchedule, ValidationReport, RealTimeValidation
)


class DataValidationRepository:
    def __init__(self):
        self._rules: Dict[UUID, ValidationRule] = {}
        self._executions: Dict[UUID, ValidationExecution] = {}
        self._results: Dict[UUID, ValidationResult] = {}
        self._errors: Dict[UUID, ValidationError] = {}
        self._schedules: Dict[UUID, ValidationSchedule] = {}
        self._reports: Dict[UUID, ValidationReport] = {}
        self._realtime_validations: Dict[UUID, RealTimeValidation] = {}

    async def save_rule(self, rule: ValidationRule) -> ValidationRule:
        self._rules[rule.rule_id] = rule
        return rule

    async def find_rule_by_id(self, rule_id: UUID) -> Optional[ValidationRule]:
        return self._rules.get(rule_id)

    async def find_all_rules(self) -> List[ValidationRule]:
        return list(self._rules.values())

    async def find_rules_by_type(self, validation_type: str) -> List[ValidationRule]:
        return [r for r in self._rules.values() if r.validation_type.value == validation_type]

    async def find_rules_by_table(self, target_table: str) -> List[ValidationRule]:
        return [r for r in self._rules.values() if r.target_table == target_table]

    async def find_active_rules(self) -> List[ValidationRule]:
        return [r for r in self._rules.values() if r.is_active]

    async def find_blocking_rules(self) -> List[ValidationRule]:
        return [r for r in self._rules.values() if r.is_blocking]

    async def delete_rule(self, rule_id: UUID) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    async def save_execution(self, execution: ValidationExecution) -> ValidationExecution:
        self._executions[execution.execution_id] = execution
        return execution

    async def find_execution_by_id(self, execution_id: UUID) -> Optional[ValidationExecution]:
        return self._executions.get(execution_id)

    async def find_all_executions(self) -> List[ValidationExecution]:
        return list(self._executions.values())

    async def find_executions_by_status(self, status: str) -> List[ValidationExecution]:
        return [e for e in self._executions.values() if e.status == status]

    async def find_executions_by_dataset(self, target_dataset: str) -> List[ValidationExecution]:
        return [e for e in self._executions.values() if e.target_dataset == target_dataset]

    async def find_running_executions(self) -> List[ValidationExecution]:
        return [e for e in self._executions.values() if e.status == "running"]

    async def save_result(self, result: ValidationResult) -> ValidationResult:
        self._results[result.result_id] = result
        return result

    async def find_result_by_id(self, result_id: UUID) -> Optional[ValidationResult]:
        return self._results.get(result_id)

    async def find_all_results(self) -> List[ValidationResult]:
        return list(self._results.values())

    async def find_results_by_execution(self, execution_id: UUID) -> List[ValidationResult]:
        return [r for r in self._results.values() if r.execution_id == execution_id]

    async def find_results_by_rule(self, rule_id: UUID) -> List[ValidationResult]:
        return [r for r in self._results.values() if r.rule_id == rule_id]

    async def find_failed_results(self) -> List[ValidationResult]:
        return [r for r in self._results.values() if r.status == "failed"]

    async def save_error(self, error: ValidationError) -> ValidationError:
        self._errors[error.error_id] = error
        return error

    async def find_error_by_id(self, error_id: UUID) -> Optional[ValidationError]:
        return self._errors.get(error_id)

    async def find_all_errors(self) -> List[ValidationError]:
        return list(self._errors.values())

    async def find_errors_by_result(self, result_id: UUID) -> List[ValidationError]:
        return [e for e in self._errors.values() if e.result_id == result_id]

    async def find_errors_by_rule(self, rule_id: UUID) -> List[ValidationError]:
        return [e for e in self._errors.values() if e.rule_id == rule_id]

    async def find_errors_by_type(self, error_type: str) -> List[ValidationError]:
        return [e for e in self._errors.values() if e.error_type == error_type]

    async def save_schedule(self, schedule: ValidationSchedule) -> ValidationSchedule:
        self._schedules[schedule.schedule_id] = schedule
        return schedule

    async def find_schedule_by_id(self, schedule_id: UUID) -> Optional[ValidationSchedule]:
        return self._schedules.get(schedule_id)

    async def find_all_schedules(self) -> List[ValidationSchedule]:
        return list(self._schedules.values())

    async def find_active_schedules(self) -> List[ValidationSchedule]:
        return [s for s in self._schedules.values() if s.is_active]

    async def find_schedules_by_dataset(self, target_dataset: str) -> List[ValidationSchedule]:
        return [s for s in self._schedules.values() if s.target_dataset == target_dataset]

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    async def save_report(self, report: ValidationReport) -> ValidationReport:
        self._reports[report.report_id] = report
        return report

    async def find_report_by_id(self, report_id: UUID) -> Optional[ValidationReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[ValidationReport]:
        return list(self._reports.values())

    async def find_reports_by_period(self, report_period: str) -> List[ValidationReport]:
        return [r for r in self._reports.values() if r.report_period == report_period]

    async def save_realtime_validation(self, validation: RealTimeValidation) -> RealTimeValidation:
        self._realtime_validations[validation.validation_id] = validation
        return validation

    async def find_realtime_validation_by_id(self, validation_id: UUID) -> Optional[RealTimeValidation]:
        return self._realtime_validations.get(validation_id)

    async def find_all_realtime_validations(self) -> List[RealTimeValidation]:
        return list(self._realtime_validations.values())

    async def find_realtime_validations_by_stream(self, stream_name: str) -> List[RealTimeValidation]:
        return [v for v in self._realtime_validations.values() if v.stream_name == stream_name]

    async def find_failed_realtime_validations(self) -> List[RealTimeValidation]:
        return [v for v in self._realtime_validations.values() if not v.is_valid]

    async def get_statistics(self) -> Dict[str, Any]:
        total_results = len(self._results)
        passed_results = len([r for r in self._results.values() if r.status == "passed"])
        return {
            "total_rules": len(self._rules),
            "active_rules": len([r for r in self._rules.values() if r.is_active]),
            "blocking_rules": len([r for r in self._rules.values() if r.is_blocking]),
            "total_executions": len(self._executions),
            "completed_executions": len([e for e in self._executions.values() if e.status == "completed"]),
            "total_results": total_results,
            "passed_results": passed_results,
            "failed_results": total_results - passed_results,
            "total_errors": len(self._errors),
            "active_schedules": len([s for s in self._schedules.values() if s.is_active]),
            "total_reports": len(self._reports),
            "realtime_validations": len(self._realtime_validations),
            "failed_realtime": len([v for v in self._realtime_validations.values() if not v.is_valid]),
        }


data_validation_repository = DataValidationRepository()
