"""Data Quality Metrics Calculator"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class QualityMetricResult:
    metric_name: str
    dimension: str
    score: Decimal
    records_evaluated: int
    records_passed: int
    records_failed: int
    calculation_time_ms: int
    calculated_at: datetime


class DataQualityMetricsCalculator:
    def __init__(self):
        self._dimension_weights = {
            "completeness": Decimal("0.20"),
            "accuracy": Decimal("0.25"),
            "consistency": Decimal("0.20"),
            "timeliness": Decimal("0.15"),
            "uniqueness": Decimal("0.10"),
            "validity": Decimal("0.10"),
        }

    def calculate_completeness(
        self, data: List[Dict[str, Any]], required_fields: List[str]
    ) -> QualityMetricResult:
        start_time = datetime.utcnow()
        total_records = len(data)
        passed_records = 0

        for record in data:
            if all(record.get(field) is not None and record.get(field) != "" for field in required_fields):
                passed_records += 1

        score = Decimal(str(passed_records / total_records * 100)) if total_records > 0 else Decimal("100")
        end_time = datetime.utcnow()
        calc_time = int((end_time - start_time).total_seconds() * 1000)

        return QualityMetricResult(
            metric_name="Completeness Check",
            dimension="completeness",
            score=score,
            records_evaluated=total_records,
            records_passed=passed_records,
            records_failed=total_records - passed_records,
            calculation_time_ms=calc_time,
            calculated_at=end_time,
        )

    def calculate_uniqueness(
        self, data: List[Dict[str, Any]], unique_fields: List[str]
    ) -> QualityMetricResult:
        start_time = datetime.utcnow()
        total_records = len(data)
        seen_values = set()
        duplicate_count = 0

        for record in data:
            key = tuple(str(record.get(field, "")) for field in unique_fields)
            if key in seen_values:
                duplicate_count += 1
            else:
                seen_values.add(key)

        passed_records = total_records - duplicate_count
        score = Decimal(str(passed_records / total_records * 100)) if total_records > 0 else Decimal("100")
        end_time = datetime.utcnow()
        calc_time = int((end_time - start_time).total_seconds() * 1000)

        return QualityMetricResult(
            metric_name="Uniqueness Check",
            dimension="uniqueness",
            score=score,
            records_evaluated=total_records,
            records_passed=passed_records,
            records_failed=duplicate_count,
            calculation_time_ms=calc_time,
            calculated_at=end_time,
        )

    def calculate_validity(
        self, data: List[Dict[str, Any]], validation_rules: Dict[str, callable]
    ) -> QualityMetricResult:
        start_time = datetime.utcnow()
        total_records = len(data)
        passed_records = 0

        for record in data:
            is_valid = True
            for field, validator in validation_rules.items():
                value = record.get(field)
                try:
                    if not validator(value):
                        is_valid = False
                        break
                except Exception:
                    is_valid = False
                    break
            if is_valid:
                passed_records += 1

        score = Decimal(str(passed_records / total_records * 100)) if total_records > 0 else Decimal("100")
        end_time = datetime.utcnow()
        calc_time = int((end_time - start_time).total_seconds() * 1000)

        return QualityMetricResult(
            metric_name="Validity Check",
            dimension="validity",
            score=score,
            records_evaluated=total_records,
            records_passed=passed_records,
            records_failed=total_records - passed_records,
            calculation_time_ms=calc_time,
            calculated_at=end_time,
        )

    def calculate_timeliness(
        self, data: List[Dict[str, Any]], date_field: str, max_age_days: int
    ) -> QualityMetricResult:
        start_time = datetime.utcnow()
        total_records = len(data)
        passed_records = 0
        today = date.today()

        for record in data:
            date_value = record.get(date_field)
            if date_value:
                if isinstance(date_value, str):
                    try:
                        date_value = datetime.fromisoformat(date_value).date()
                    except ValueError:
                        continue
                elif isinstance(date_value, datetime):
                    date_value = date_value.date()

                if isinstance(date_value, date):
                    age = (today - date_value).days
                    if age <= max_age_days:
                        passed_records += 1

        score = Decimal(str(passed_records / total_records * 100)) if total_records > 0 else Decimal("100")
        end_time = datetime.utcnow()
        calc_time = int((end_time - start_time).total_seconds() * 1000)

        return QualityMetricResult(
            metric_name="Timeliness Check",
            dimension="timeliness",
            score=score,
            records_evaluated=total_records,
            records_passed=passed_records,
            records_failed=total_records - passed_records,
            calculation_time_ms=calc_time,
            calculated_at=end_time,
        )

    def calculate_overall_score(self, dimension_scores: Dict[str, Decimal]) -> Decimal:
        weighted_sum = Decimal("0")
        total_weight = Decimal("0")

        for dimension, score in dimension_scores.items():
            weight = self._dimension_weights.get(dimension, Decimal("0.1"))
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else Decimal("0")

    def set_dimension_weight(self, dimension: str, weight: Decimal) -> None:
        self._dimension_weights[dimension] = weight

    def get_dimension_weights(self) -> Dict[str, Decimal]:
        return self._dimension_weights.copy()


data_quality_metrics_calculator = DataQualityMetricsCalculator()
