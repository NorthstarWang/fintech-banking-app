"""Data Accuracy Analysis Utilities"""

from typing import List, Dict, Any, Optional, Callable
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class AccuracyRule:
    rule_id: str
    rule_name: str
    field_name: str
    accuracy_type: str
    reference_source: str
    parameters: Dict[str, Any]


@dataclass
class AccuracyDiscrepancy:
    discrepancy_id: str
    rule_id: str
    record_id: str
    field_name: str
    actual_value: Any
    expected_value: Any
    discrepancy_type: str
    severity: str


@dataclass
class AccuracyCheckResult:
    check_id: str
    rule: AccuracyRule
    total_records: int
    accurate_records: int
    inaccurate_records: int
    accuracy_rate: Decimal
    discrepancies: List[AccuracyDiscrepancy]
    checked_at: datetime


class DataAccuracyUtilities:
    def __init__(self):
        self._rules: Dict[str, AccuracyRule] = {}
        self._reference_data: Dict[str, Dict[str, Any]] = {}
        self._accuracy_validators: Dict[str, Callable] = {}
        self._register_default_validators()

    def _register_default_validators(self) -> None:
        self._accuracy_validators["exact_match"] = self._validate_exact_match
        self._accuracy_validators["range_check"] = self._validate_range_check
        self._accuracy_validators["reference_lookup"] = self._validate_reference_lookup
        self._accuracy_validators["format_check"] = self._validate_format_check
        self._accuracy_validators["business_rule"] = self._validate_business_rule
        self._accuracy_validators["cross_reference"] = self._validate_cross_reference

    def register_reference_data(
        self,
        source_name: str,
        data: Dict[str, Any],
    ) -> None:
        self._reference_data[source_name] = data

    def create_rule(
        self,
        rule_name: str,
        field_name: str,
        accuracy_type: str,
        reference_source: str = "",
        parameters: Dict[str, Any] = None,
    ) -> AccuracyRule:
        rule = AccuracyRule(
            rule_id=str(uuid4()),
            rule_name=rule_name,
            field_name=field_name,
            accuracy_type=accuracy_type,
            reference_source=reference_source,
            parameters=parameters or {},
        )
        self._rules[rule.rule_id] = rule
        return rule

    def check_accuracy(
        self,
        data: List[Dict[str, Any]],
        rule: AccuracyRule,
        id_field: str = "id",
    ) -> AccuracyCheckResult:
        validator = self._accuracy_validators.get(rule.accuracy_type)
        if not validator:
            return AccuracyCheckResult(
                check_id=str(uuid4()),
                rule=rule,
                total_records=len(data),
                accurate_records=len(data),
                inaccurate_records=0,
                accuracy_rate=Decimal("100"),
                discrepancies=[],
                checked_at=datetime.utcnow(),
            )

        discrepancies = []
        accurate_count = 0

        for i, record in enumerate(data):
            record_id = str(record.get(id_field, i))
            is_accurate, expected, discrepancy_type = validator(record, rule)

            if is_accurate:
                accurate_count += 1
            else:
                actual_value = record.get(rule.field_name)
                discrepancies.append(
                    AccuracyDiscrepancy(
                        discrepancy_id=str(uuid4()),
                        rule_id=rule.rule_id,
                        record_id=record_id,
                        field_name=rule.field_name,
                        actual_value=actual_value,
                        expected_value=expected,
                        discrepancy_type=discrepancy_type,
                        severity="high" if discrepancy_type in ["missing_reference", "business_rule_violation"] else "medium",
                    )
                )

        total = len(data)
        accuracy_rate = Decimal(str(accurate_count / total * 100)) if total > 0 else Decimal("100")

        return AccuracyCheckResult(
            check_id=str(uuid4()),
            rule=rule,
            total_records=total,
            accurate_records=accurate_count,
            inaccurate_records=total - accurate_count,
            accuracy_rate=accuracy_rate,
            discrepancies=discrepancies,
            checked_at=datetime.utcnow(),
        )

    def _validate_exact_match(
        self, record: Dict[str, Any], rule: AccuracyRule
    ) -> tuple:
        actual = record.get(rule.field_name)
        expected = rule.parameters.get("expected_value")

        if actual == expected:
            return True, expected, ""
        return False, expected, "value_mismatch"

    def _validate_range_check(
        self, record: Dict[str, Any], rule: AccuracyRule
    ) -> tuple:
        actual = record.get(rule.field_name)
        min_val = rule.parameters.get("min_value")
        max_val = rule.parameters.get("max_value")

        if actual is None:
            return True, None, ""

        try:
            num_val = float(actual)
            if min_val is not None and num_val < float(min_val):
                return False, f">= {min_val}", "below_minimum"
            if max_val is not None and num_val > float(max_val):
                return False, f"<= {max_val}", "above_maximum"
            return True, f"{min_val}-{max_val}", ""
        except (ValueError, TypeError):
            return False, "numeric", "non_numeric_value"

    def _validate_reference_lookup(
        self, record: Dict[str, Any], rule: AccuracyRule
    ) -> tuple:
        actual = record.get(rule.field_name)
        reference_source = rule.reference_source
        lookup_key = rule.parameters.get("lookup_key", rule.field_name)
        lookup_field = rule.parameters.get("lookup_field")

        reference = self._reference_data.get(reference_source, {})
        if not reference:
            return True, None, ""

        key_value = record.get(lookup_key)
        if key_value not in reference:
            return False, "valid_reference", "missing_reference"

        if lookup_field:
            expected = reference[key_value].get(lookup_field)
            if actual != expected:
                return False, expected, "reference_mismatch"

        return True, actual, ""

    def _validate_format_check(
        self, record: Dict[str, Any], rule: AccuracyRule
    ) -> tuple:
        import re
        actual = record.get(rule.field_name)
        pattern = rule.parameters.get("pattern")

        if actual is None or pattern is None:
            return True, None, ""

        if re.match(pattern, str(actual)):
            return True, pattern, ""
        return False, f"pattern: {pattern}", "format_violation"

    def _validate_business_rule(
        self, record: Dict[str, Any], rule: AccuracyRule
    ) -> tuple:
        rule_expression = rule.parameters.get("expression")
        if not rule_expression:
            return True, None, ""

        try:
            result = eval(rule_expression, {"__builtins__": {}}, {"record": record})
            if result:
                return True, "business_rule_passed", ""
            return False, rule_expression, "business_rule_violation"
        except Exception:
            return False, rule_expression, "rule_evaluation_error"

    def _validate_cross_reference(
        self, record: Dict[str, Any], rule: AccuracyRule
    ) -> tuple:
        source_field = rule.field_name
        target_field = rule.parameters.get("target_field")
        relationship = rule.parameters.get("relationship", "equal")

        source_val = record.get(source_field)
        target_val = record.get(target_field)

        if source_val is None or target_val is None:
            return True, None, ""

        if relationship == "equal" and source_val != target_val:
            return False, target_val, "cross_reference_mismatch"
        elif relationship == "less_than":
            try:
                if float(source_val) >= float(target_val):
                    return False, f"< {target_val}", "cross_reference_violation"
            except (ValueError, TypeError):
                pass

        return True, target_val, ""

    def get_rules(self) -> Dict[str, AccuracyRule]:
        return self._rules.copy()

    def register_validator(self, name: str, validator: Callable) -> None:
        self._accuracy_validators[name] = validator


data_accuracy_utilities = DataAccuracyUtilities()
