"""Data Completeness Analysis Utilities"""

from typing import List, Dict, Any, Optional, Set
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class FieldCompletenessResult:
    field_name: str
    total_records: int
    non_null_count: int
    null_count: int
    empty_count: int
    completeness_rate: Decimal
    is_required: bool
    passes_threshold: bool


@dataclass
class RecordCompletenessResult:
    record_id: str
    total_fields: int
    complete_fields: int
    incomplete_fields: List[str]
    completeness_rate: Decimal


@dataclass
class DatasetCompletenessReport:
    report_id: str
    dataset_name: str
    total_records: int
    total_fields: int
    overall_completeness: Decimal
    field_results: List[FieldCompletenessResult]
    incomplete_records_count: int
    fully_complete_records_count: int
    analyzed_at: datetime


class DataCompletenessUtilities:
    def __init__(self):
        self._required_fields: Dict[str, Set[str]] = {}
        self._field_thresholds: Dict[str, Decimal] = {}
        self._default_threshold = Decimal("95")

    def analyze_field_completeness(
        self,
        data: List[Dict[str, Any]],
        field_name: str,
        is_required: bool = False,
        threshold: Decimal = None,
    ) -> FieldCompletenessResult:
        total = len(data)
        null_count = 0
        empty_count = 0

        for record in data:
            value = record.get(field_name)
            if value is None:
                null_count += 1
            elif value == "" or (isinstance(value, str) and value.strip() == ""):
                empty_count += 1

        non_null_count = total - null_count - empty_count
        completeness_rate = Decimal(str(non_null_count / total * 100)) if total > 0 else Decimal("100")

        effective_threshold = threshold or self._field_thresholds.get(field_name, self._default_threshold)
        passes_threshold = completeness_rate >= effective_threshold

        return FieldCompletenessResult(
            field_name=field_name,
            total_records=total,
            non_null_count=non_null_count,
            null_count=null_count,
            empty_count=empty_count,
            completeness_rate=completeness_rate,
            is_required=is_required,
            passes_threshold=passes_threshold,
        )

    def analyze_record_completeness(
        self,
        record: Dict[str, Any],
        record_id: str = "",
        required_fields: List[str] = None,
    ) -> RecordCompletenessResult:
        fields_to_check = required_fields or list(record.keys())
        total_fields = len(fields_to_check)
        complete_count = 0
        incomplete = []

        for field_name in fields_to_check:
            value = record.get(field_name)
            if value is not None and value != "" and not (isinstance(value, str) and value.strip() == ""):
                complete_count += 1
            else:
                incomplete.append(field_name)

        completeness_rate = Decimal(str(complete_count / total_fields * 100)) if total_fields > 0 else Decimal("100")

        return RecordCompletenessResult(
            record_id=record_id,
            total_fields=total_fields,
            complete_fields=complete_count,
            incomplete_fields=incomplete,
            completeness_rate=completeness_rate,
        )

    def analyze_dataset_completeness(
        self,
        data: List[Dict[str, Any]],
        dataset_name: str = "dataset",
        required_fields: List[str] = None,
        id_field: str = "id",
    ) -> DatasetCompletenessReport:
        if not data:
            return DatasetCompletenessReport(
                report_id=str(uuid4()),
                dataset_name=dataset_name,
                total_records=0,
                total_fields=0,
                overall_completeness=Decimal("100"),
                field_results=[],
                incomplete_records_count=0,
                fully_complete_records_count=0,
                analyzed_at=datetime.utcnow(),
            )

        all_fields = set()
        for record in data:
            all_fields.update(record.keys())

        fields_to_analyze = list(all_fields)
        required = set(required_fields) if required_fields else set()

        field_results = []
        for field_name in fields_to_analyze:
            result = self.analyze_field_completeness(
                data,
                field_name,
                is_required=field_name in required,
            )
            field_results.append(result)

        total_cells = len(data) * len(fields_to_analyze)
        complete_cells = sum(r.non_null_count for r in field_results)
        overall_completeness = Decimal(str(complete_cells / total_cells * 100)) if total_cells > 0 else Decimal("100")

        incomplete_records = 0
        fully_complete = 0

        for record in data:
            record_result = self.analyze_record_completeness(
                record,
                required_fields=required_fields,
            )
            if record_result.completeness_rate < Decimal("100"):
                incomplete_records += 1
            else:
                fully_complete += 1

        return DatasetCompletenessReport(
            report_id=str(uuid4()),
            dataset_name=dataset_name,
            total_records=len(data),
            total_fields=len(fields_to_analyze),
            overall_completeness=overall_completeness,
            field_results=field_results,
            incomplete_records_count=incomplete_records,
            fully_complete_records_count=fully_complete,
            analyzed_at=datetime.utcnow(),
        )

    def find_incomplete_records(
        self,
        data: List[Dict[str, Any]],
        required_fields: List[str],
        id_field: str = "id",
        threshold: Decimal = Decimal("100"),
    ) -> List[RecordCompletenessResult]:
        incomplete = []

        for i, record in enumerate(data):
            record_id = str(record.get(id_field, i))
            result = self.analyze_record_completeness(record, record_id, required_fields)
            if result.completeness_rate < threshold:
                incomplete.append(result)

        return incomplete

    def get_completeness_trend(
        self,
        historical_reports: List[DatasetCompletenessReport],
    ) -> List[Dict[str, Any]]:
        trend = []
        for report in sorted(historical_reports, key=lambda r: r.analyzed_at):
            trend.append({
                "date": report.analyzed_at.isoformat(),
                "overall_completeness": float(report.overall_completeness),
                "total_records": report.total_records,
                "incomplete_records": report.incomplete_records_count,
            })
        return trend

    def set_required_fields(self, dataset_name: str, fields: List[str]) -> None:
        self._required_fields[dataset_name] = set(fields)

    def get_required_fields(self, dataset_name: str) -> Set[str]:
        return self._required_fields.get(dataset_name, set())

    def set_field_threshold(self, field_name: str, threshold: Decimal) -> None:
        self._field_thresholds[field_name] = threshold

    def set_default_threshold(self, threshold: Decimal) -> None:
        self._default_threshold = threshold


data_completeness_utilities = DataCompletenessUtilities()
