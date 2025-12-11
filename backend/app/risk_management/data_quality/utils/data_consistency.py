"""Data Consistency Analysis Utilities"""

from typing import List, Dict, Any, Optional, Set, Tuple
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class ConsistencyRule:
    rule_id: str
    rule_name: str
    rule_type: str
    source_fields: List[str]
    parameters: Dict[str, Any]
    error_message: str


@dataclass
class ConsistencyViolation:
    violation_id: str
    rule_id: str
    rule_name: str
    record_id: str
    field_values: Dict[str, Any]
    violation_details: str
    severity: str


@dataclass
class ConsistencyCheckResult:
    check_id: str
    rule: ConsistencyRule
    total_records: int
    consistent_records: int
    inconsistent_records: int
    consistency_rate: Decimal
    violations: List[ConsistencyViolation]
    checked_at: datetime


class DataConsistencyUtilities:
    def __init__(self):
        self._rules: Dict[str, ConsistencyRule] = {}
        self._cross_field_validators: Dict[str, callable] = {}
        self._register_default_validators()

    def _register_default_validators(self) -> None:
        self._cross_field_validators["date_order"] = self._validate_date_order
        self._cross_field_validators["numeric_comparison"] = self._validate_numeric_comparison
        self._cross_field_validators["conditional_required"] = self._validate_conditional_required
        self._cross_field_validators["mutual_exclusion"] = self._validate_mutual_exclusion
        self._cross_field_validators["sum_equals"] = self._validate_sum_equals

    def create_rule(
        self,
        rule_name: str,
        rule_type: str,
        source_fields: List[str],
        parameters: Dict[str, Any] = None,
        error_message: str = "",
    ) -> ConsistencyRule:
        rule = ConsistencyRule(
            rule_id=str(uuid4()),
            rule_name=rule_name,
            rule_type=rule_type,
            source_fields=source_fields,
            parameters=parameters or {},
            error_message=error_message or f"Consistency violation in {rule_name}",
        )
        self._rules[rule.rule_id] = rule
        return rule

    def check_consistency(
        self,
        data: List[Dict[str, Any]],
        rule: ConsistencyRule,
        id_field: str = "id",
    ) -> ConsistencyCheckResult:
        validator = self._cross_field_validators.get(rule.rule_type)
        if not validator:
            return ConsistencyCheckResult(
                check_id=str(uuid4()),
                rule=rule,
                total_records=len(data),
                consistent_records=len(data),
                inconsistent_records=0,
                consistency_rate=Decimal("100"),
                violations=[],
                checked_at=datetime.utcnow(),
            )

        violations = []
        consistent_count = 0

        for i, record in enumerate(data):
            record_id = str(record.get(id_field, i))
            is_consistent, violation_detail = validator(record, rule)

            if is_consistent:
                consistent_count += 1
            else:
                violations.append(
                    ConsistencyViolation(
                        violation_id=str(uuid4()),
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        record_id=record_id,
                        field_values={f: record.get(f) for f in rule.source_fields},
                        violation_details=violation_detail,
                        severity="high" if rule.rule_type in ["date_order", "sum_equals"] else "medium",
                    )
                )

        total = len(data)
        consistency_rate = Decimal(str(consistent_count / total * 100)) if total > 0 else Decimal("100")

        return ConsistencyCheckResult(
            check_id=str(uuid4()),
            rule=rule,
            total_records=total,
            consistent_records=consistent_count,
            inconsistent_records=total - consistent_count,
            consistency_rate=consistency_rate,
            violations=violations,
            checked_at=datetime.utcnow(),
        )

    def check_all_rules(
        self,
        data: List[Dict[str, Any]],
        id_field: str = "id",
    ) -> List[ConsistencyCheckResult]:
        results = []
        for rule in self._rules.values():
            result = self.check_consistency(data, rule, id_field)
            results.append(result)
        return results

    def _validate_date_order(
        self, record: Dict[str, Any], rule: ConsistencyRule
    ) -> Tuple[bool, str]:
        fields = rule.source_fields
        if len(fields) < 2:
            return True, ""

        start_field = fields[0]
        end_field = fields[1]

        start_value = record.get(start_field)
        end_value = record.get(end_field)

        if start_value is None or end_value is None:
            return True, ""

        try:
            if isinstance(start_value, str):
                start_value = datetime.fromisoformat(start_value)
            if isinstance(end_value, str):
                end_value = datetime.fromisoformat(end_value)

            if start_value > end_value:
                return False, f"{start_field} ({start_value}) is after {end_field} ({end_value})"
        except (ValueError, TypeError):
            return False, f"Invalid date values in {start_field} or {end_field}"

        return True, ""

    def _validate_numeric_comparison(
        self, record: Dict[str, Any], rule: ConsistencyRule
    ) -> Tuple[bool, str]:
        fields = rule.source_fields
        if len(fields) < 2:
            return True, ""

        operator = rule.parameters.get("operator", "<=")
        field1 = fields[0]
        field2 = fields[1]

        val1 = record.get(field1)
        val2 = record.get(field2)

        if val1 is None or val2 is None:
            return True, ""

        try:
            num1 = float(val1)
            num2 = float(val2)

            if operator == "<=" and num1 > num2:
                return False, f"{field1} ({num1}) > {field2} ({num2})"
            elif operator == "<" and num1 >= num2:
                return False, f"{field1} ({num1}) >= {field2} ({num2})"
            elif operator == ">=" and num1 < num2:
                return False, f"{field1} ({num1}) < {field2} ({num2})"
            elif operator == ">" and num1 <= num2:
                return False, f"{field1} ({num1}) <= {field2} ({num2})"
            elif operator == "==" and num1 != num2:
                return False, f"{field1} ({num1}) != {field2} ({num2})"
        except (ValueError, TypeError):
            return False, f"Non-numeric values in {field1} or {field2}"

        return True, ""

    def _validate_conditional_required(
        self, record: Dict[str, Any], rule: ConsistencyRule
    ) -> Tuple[bool, str]:
        condition_field = rule.parameters.get("condition_field")
        condition_value = rule.parameters.get("condition_value")
        required_fields = rule.source_fields

        if not condition_field:
            return True, ""

        if record.get(condition_field) == condition_value:
            for field in required_fields:
                value = record.get(field)
                if value is None or value == "":
                    return False, f"{field} is required when {condition_field}={condition_value}"

        return True, ""

    def _validate_mutual_exclusion(
        self, record: Dict[str, Any], rule: ConsistencyRule
    ) -> Tuple[bool, str]:
        fields = rule.source_fields
        non_null_count = 0

        for field in fields:
            value = record.get(field)
            if value is not None and value != "":
                non_null_count += 1

        max_allowed = rule.parameters.get("max_allowed", 1)

        if non_null_count > max_allowed:
            return False, f"Only {max_allowed} of {fields} should have values, found {non_null_count}"

        return True, ""

    def _validate_sum_equals(
        self, record: Dict[str, Any], rule: ConsistencyRule
    ) -> Tuple[bool, str]:
        sum_fields = rule.source_fields[:-1]
        total_field = rule.source_fields[-1]
        tolerance = float(rule.parameters.get("tolerance", 0.01))

        try:
            calculated_sum = sum(float(record.get(f, 0) or 0) for f in sum_fields)
            expected_total = float(record.get(total_field, 0) or 0)

            if abs(calculated_sum - expected_total) > tolerance:
                return False, f"Sum of {sum_fields} ({calculated_sum}) != {total_field} ({expected_total})"
        except (ValueError, TypeError):
            return False, f"Non-numeric values in sum calculation"

        return True, ""

    def get_rules(self) -> Dict[str, ConsistencyRule]:
        return self._rules.copy()

    def register_validator(self, name: str, validator: callable) -> None:
        self._cross_field_validators[name] = validator


data_consistency_utilities = DataConsistencyUtilities()
