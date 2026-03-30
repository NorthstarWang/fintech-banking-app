"""Data Profiling Utilities"""

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class ColumnStatistics:
    column_name: str
    data_type: str
    total_count: int
    null_count: int
    distinct_count: int
    min_value: str | None
    max_value: str | None
    avg_value: Decimal | None
    std_dev: Decimal | None
    median_value: str | None
    mode_value: str | None
    empty_string_count: int


@dataclass
class PatternDetectionResult:
    pattern_name: str
    pattern_regex: str
    match_count: int
    match_percentage: Decimal
    sample_matches: list[str]


class DataProfilingUtilities:
    def __init__(self):
        self._common_patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone_us": r"^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$",
            "ssn": r"^\d{3}-\d{2}-\d{4}$",
            "zip_code": r"^\d{5}(-\d{4})?$",
            "credit_card": r"^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$",
            "date_iso": r"^\d{4}-\d{2}-\d{2}$",
            "date_us": r"^\d{2}/\d{2}/\d{4}$",
            "currency": r"^\$?\d{1,3}(,\d{3})*(\.\d{2})?$",
            "percentage": r"^\d+(\.\d+)?%$",
            "uuid": r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
            "ipv4": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            "url": r"^https?://[^\s]+$",
        }

    def profile_column(self, data: list[Any], column_name: str) -> ColumnStatistics:
        total_count = len(data)
        null_count = sum(1 for v in data if v is None)
        empty_count = sum(1 for v in data if v == "")
        non_null_data = [v for v in data if v is not None and v != ""]

        distinct_count = len({str(v) for v in non_null_data})

        min_val = None
        max_val = None
        avg_val = None
        std_dev = None
        median_val = None
        mode_val = None
        data_type = "unknown"

        if non_null_data:
            first_val = non_null_data[0]
            if isinstance(first_val, (int, float, Decimal)):
                data_type = "numeric"
                numeric_data = [float(v) for v in non_null_data if isinstance(v, (int, float, Decimal))]
                if numeric_data:
                    min_val = str(min(numeric_data))
                    max_val = str(max(numeric_data))
                    avg_val = Decimal(str(sum(numeric_data) / len(numeric_data)))
                    sorted_data = sorted(numeric_data)
                    mid = len(sorted_data) // 2
                    median_val = str(sorted_data[mid])
            elif isinstance(first_val, str):
                data_type = "string"
                str_data = [str(v) for v in non_null_data]
                if str_data:
                    min_val = min(str_data)
                    max_val = max(str_data)
            elif isinstance(first_val, datetime):
                data_type = "datetime"
                date_data = [v for v in non_null_data if isinstance(v, datetime)]
                if date_data:
                    min_val = str(min(date_data))
                    max_val = str(max(date_data))

            counter = Counter(str(v) for v in non_null_data)
            most_common = counter.most_common(1)
            if most_common:
                mode_val = most_common[0][0]

        return ColumnStatistics(
            column_name=column_name,
            data_type=data_type,
            total_count=total_count,
            null_count=null_count,
            distinct_count=distinct_count,
            min_value=min_val,
            max_value=max_val,
            avg_value=avg_val,
            std_dev=std_dev,
            median_value=median_val,
            mode_value=mode_val,
            empty_string_count=empty_count,
        )

    def detect_patterns(self, data: list[str], max_samples: int = 5) -> list[PatternDetectionResult]:
        results = []
        total_count = len(data)

        for pattern_name, pattern_regex in self._common_patterns.items():
            compiled_pattern = re.compile(pattern_regex, re.IGNORECASE)
            matches = [v for v in data if v and compiled_pattern.match(str(v))]
            match_count = len(matches)

            if match_count > 0:
                match_percentage = Decimal(str(match_count / total_count * 100))
                results.append(
                    PatternDetectionResult(
                        pattern_name=pattern_name,
                        pattern_regex=pattern_regex,
                        match_count=match_count,
                        match_percentage=match_percentage,
                        sample_matches=matches[:max_samples],
                    )
                )

        return sorted(results, key=lambda x: x.match_count, reverse=True)

    def detect_data_type(self, data: list[Any]) -> str:
        non_null_data = [v for v in data if v is not None and v != ""]
        if not non_null_data:
            return "unknown"

        type_counts = Counter()
        for value in non_null_data:
            if isinstance(value, bool):
                type_counts["boolean"] += 1
            elif isinstance(value, int):
                type_counts["integer"] += 1
            elif isinstance(value, float):
                type_counts["float"] += 1
            elif isinstance(value, Decimal):
                type_counts["decimal"] += 1
            elif isinstance(value, datetime):
                type_counts["datetime"] += 1
            elif isinstance(value, str):
                type_counts["string"] += 1
            else:
                type_counts["unknown"] += 1

        most_common = type_counts.most_common(1)
        return most_common[0][0] if most_common else "unknown"

    def calculate_cardinality_ratio(self, distinct_count: int, total_count: int) -> tuple[str, Decimal]:
        if total_count == 0:
            return "empty", Decimal("0")

        ratio = Decimal(str(distinct_count / total_count))

        if ratio == 1:
            return "unique", ratio
        if ratio > Decimal("0.9"):
            return "high_cardinality", ratio
        if ratio > Decimal("0.5"):
            return "medium_cardinality", ratio
        if ratio > Decimal("0.1"):
            return "low_cardinality", ratio
        return "categorical", ratio

    def detect_outliers_iqr(self, data: list[float], multiplier: float = 1.5) -> list[float]:
        if len(data) < 4:
            return []

        sorted_data = sorted(data)
        n = len(sorted_data)
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        q1 = sorted_data[q1_idx]
        q3 = sorted_data[q3_idx]
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        return [v for v in data if v < lower_bound or v > upper_bound]

    def add_custom_pattern(self, pattern_name: str, pattern_regex: str) -> None:
        self._common_patterns[pattern_name] = pattern_regex

    def get_available_patterns(self) -> dict[str, str]:
        return self._common_patterns.copy()


data_profiling_utilities = DataProfilingUtilities()
