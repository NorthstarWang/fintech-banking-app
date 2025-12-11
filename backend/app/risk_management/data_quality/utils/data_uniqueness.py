"""Data Uniqueness Analysis Utilities"""

from typing import List, Dict, Any, Optional, Set, Tuple
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from collections import Counter
from uuid import uuid4


@dataclass
class DuplicateGroup:
    group_id: str
    key_value: str
    duplicate_count: int
    record_ids: List[str]
    first_occurrence_id: str


@dataclass
class UniquenessCheckResult:
    check_id: str
    field_name: str
    total_records: int
    unique_records: int
    duplicate_records: int
    uniqueness_rate: Decimal
    distinct_values: int
    duplicate_groups: List[DuplicateGroup]
    checked_at: datetime


@dataclass
class CompositeUniquenessResult:
    check_id: str
    key_fields: List[str]
    total_records: int
    unique_combinations: int
    duplicate_combinations: int
    uniqueness_rate: Decimal
    duplicate_groups: List[DuplicateGroup]
    checked_at: datetime


class DataUniquenessUtilities:
    def __init__(self):
        self._unique_constraints: Dict[str, List[str]] = {}

    def check_field_uniqueness(
        self,
        data: List[Dict[str, Any]],
        field_name: str,
        id_field: str = "id",
    ) -> UniquenessCheckResult:
        value_records: Dict[str, List[str]] = {}

        for i, record in enumerate(data):
            record_id = str(record.get(id_field, i))
            value = record.get(field_name)
            key = str(value) if value is not None else "__NULL__"

            if key not in value_records:
                value_records[key] = []
            value_records[key].append(record_id)

        duplicate_groups = []
        duplicate_count = 0
        unique_count = 0

        for key, record_ids in value_records.items():
            if len(record_ids) > 1:
                duplicate_count += len(record_ids) - 1
                unique_count += 1
                duplicate_groups.append(
                    DuplicateGroup(
                        group_id=str(uuid4()),
                        key_value=key,
                        duplicate_count=len(record_ids),
                        record_ids=record_ids,
                        first_occurrence_id=record_ids[0],
                    )
                )
            else:
                unique_count += 1

        total = len(data)
        unique_records = total - duplicate_count
        uniqueness_rate = Decimal(str(unique_records / total * 100)) if total > 0 else Decimal("100")

        return UniquenessCheckResult(
            check_id=str(uuid4()),
            field_name=field_name,
            total_records=total,
            unique_records=unique_records,
            duplicate_records=duplicate_count,
            uniqueness_rate=uniqueness_rate,
            distinct_values=len(value_records),
            duplicate_groups=duplicate_groups,
            checked_at=datetime.utcnow(),
        )

    def check_composite_uniqueness(
        self,
        data: List[Dict[str, Any]],
        key_fields: List[str],
        id_field: str = "id",
    ) -> CompositeUniquenessResult:
        key_records: Dict[tuple, List[str]] = {}

        for i, record in enumerate(data):
            record_id = str(record.get(id_field, i))
            key = tuple(
                str(record.get(f)) if record.get(f) is not None else "__NULL__"
                for f in key_fields
            )

            if key not in key_records:
                key_records[key] = []
            key_records[key].append(record_id)

        duplicate_groups = []
        duplicate_count = 0

        for key, record_ids in key_records.items():
            if len(record_ids) > 1:
                duplicate_count += len(record_ids) - 1
                duplicate_groups.append(
                    DuplicateGroup(
                        group_id=str(uuid4()),
                        key_value=str(key),
                        duplicate_count=len(record_ids),
                        record_ids=record_ids,
                        first_occurrence_id=record_ids[0],
                    )
                )

        total = len(data)
        unique_combinations = len(key_records)
        duplicate_combinations = len(duplicate_groups)
        uniqueness_rate = Decimal(str((total - duplicate_count) / total * 100)) if total > 0 else Decimal("100")

        return CompositeUniquenessResult(
            check_id=str(uuid4()),
            key_fields=key_fields,
            total_records=total,
            unique_combinations=unique_combinations,
            duplicate_combinations=duplicate_combinations,
            uniqueness_rate=uniqueness_rate,
            duplicate_groups=duplicate_groups,
            checked_at=datetime.utcnow(),
        )

    def find_near_duplicates(
        self,
        data: List[Dict[str, Any]],
        compare_fields: List[str],
        similarity_threshold: Decimal = Decimal("0.9"),
        id_field: str = "id",
    ) -> List[Tuple[str, str, Decimal]]:
        near_duplicates = []

        for i in range(len(data)):
            for j in range(i + 1, len(data)):
                record1 = data[i]
                record2 = data[j]

                similarity = self._calculate_record_similarity(
                    record1, record2, compare_fields
                )

                if similarity >= similarity_threshold:
                    id1 = str(record1.get(id_field, i))
                    id2 = str(record2.get(id_field, j))
                    near_duplicates.append((id1, id2, similarity))

        return near_duplicates

    def _calculate_record_similarity(
        self,
        record1: Dict[str, Any],
        record2: Dict[str, Any],
        fields: List[str],
    ) -> Decimal:
        if not fields:
            return Decimal("0")

        total_similarity = Decimal("0")
        for field in fields:
            val1 = str(record1.get(field, ""))
            val2 = str(record2.get(field, ""))
            total_similarity += self._string_similarity(val1, val2)

        return total_similarity / Decimal(str(len(fields)))

    def _string_similarity(self, s1: str, s2: str) -> Decimal:
        if s1 == s2:
            return Decimal("1")
        if not s1 or not s2:
            return Decimal("0")

        s1 = s1.lower()
        s2 = s2.lower()

        if len(s1) < len(s2):
            s1, s2 = s2, s1

        previous = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous[j + 1] + 1
                deletions = current[j] + 1
                substitutions = previous[j] + (c1 != c2)
                current.append(min(insertions, deletions, substitutions))
            previous = current

        distance = previous[-1]
        max_len = max(len(s1), len(s2))
        return Decimal(str(round(1 - (distance / max_len), 4)))

    def get_value_frequency(
        self,
        data: List[Dict[str, Any]],
        field_name: str,
        top_n: int = 10,
    ) -> List[Tuple[Any, int, Decimal]]:
        values = [record.get(field_name) for record in data]
        counter = Counter(values)
        total = len(values)

        frequency_list = []
        for value, count in counter.most_common(top_n):
            percentage = Decimal(str(count / total * 100)) if total > 0 else Decimal("0")
            frequency_list.append((value, count, percentage))

        return frequency_list

    def register_unique_constraint(
        self,
        constraint_name: str,
        fields: List[str],
    ) -> None:
        self._unique_constraints[constraint_name] = fields

    def validate_unique_constraints(
        self,
        data: List[Dict[str, Any]],
        id_field: str = "id",
    ) -> Dict[str, CompositeUniquenessResult]:
        results = {}
        for constraint_name, fields in self._unique_constraints.items():
            result = self.check_composite_uniqueness(data, fields, id_field)
            results[constraint_name] = result
        return results

    def get_constraints(self) -> Dict[str, List[str]]:
        return self._unique_constraints.copy()


data_uniqueness_utilities = DataUniquenessUtilities()
