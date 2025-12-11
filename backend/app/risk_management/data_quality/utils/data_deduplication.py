"""Data Deduplication Utilities"""

from typing import List, Dict, Any, Optional, Set, Tuple
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
from uuid import uuid4


@dataclass
class DuplicateGroup:
    group_id: str
    primary_record: Dict[str, Any]
    duplicate_records: List[Dict[str, Any]]
    match_score: Decimal
    matched_fields: List[str]
    identified_at: datetime


@dataclass
class DeduplicationResult:
    total_records: int
    unique_records: int
    duplicate_groups: int
    records_removed: int
    duplicate_groups_list: List[DuplicateGroup]
    processing_time_ms: int
    processed_at: datetime


class DataDeduplicationUtilities:
    def __init__(self):
        self._default_threshold = Decimal("1.0")
        self._survivorship_rules: Dict[str, str] = {}

    def find_exact_duplicates(
        self,
        data: List[Dict[str, Any]],
        key_fields: List[str],
        id_field: str = "id",
    ) -> DeduplicationResult:
        start_time = datetime.utcnow()
        groups_by_key: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)

        for record in data:
            key = tuple(str(record.get(f, "")).lower().strip() for f in key_fields)
            groups_by_key[key].append(record)

        duplicate_groups = []
        total_duplicates = 0

        for key, records in groups_by_key.items():
            if len(records) > 1:
                primary = self._select_primary_record(records, id_field)
                duplicates = [r for r in records if r.get(id_field) != primary.get(id_field)]
                total_duplicates += len(duplicates)

                duplicate_groups.append(
                    DuplicateGroup(
                        group_id=str(uuid4()),
                        primary_record=primary,
                        duplicate_records=duplicates,
                        match_score=Decimal("1.0"),
                        matched_fields=key_fields,
                        identified_at=datetime.utcnow(),
                    )
                )

        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        return DeduplicationResult(
            total_records=len(data),
            unique_records=len(data) - total_duplicates,
            duplicate_groups=len(duplicate_groups),
            records_removed=total_duplicates,
            duplicate_groups_list=duplicate_groups,
            processing_time_ms=processing_time,
            processed_at=end_time,
        )

    def find_fuzzy_duplicates(
        self,
        data: List[Dict[str, Any]],
        match_fields: List[str],
        threshold: Decimal = None,
        id_field: str = "id",
    ) -> DeduplicationResult:
        start_time = datetime.utcnow()
        threshold = threshold or self._default_threshold
        duplicate_groups = []
        processed_ids: Set[str] = set()
        total_duplicates = 0

        for i, record1 in enumerate(data):
            record1_id = str(record1.get(id_field, i))
            if record1_id in processed_ids:
                continue

            group_records = [record1]

            for j, record2 in enumerate(data[i + 1:], start=i + 1):
                record2_id = str(record2.get(id_field, j))
                if record2_id in processed_ids:
                    continue

                score = self._calculate_similarity(record1, record2, match_fields)
                if score >= threshold:
                    group_records.append(record2)
                    processed_ids.add(record2_id)

            if len(group_records) > 1:
                processed_ids.add(record1_id)
                primary = self._select_primary_record(group_records, id_field)
                duplicates = [r for r in group_records if r.get(id_field) != primary.get(id_field)]
                total_duplicates += len(duplicates)

                duplicate_groups.append(
                    DuplicateGroup(
                        group_id=str(uuid4()),
                        primary_record=primary,
                        duplicate_records=duplicates,
                        match_score=threshold,
                        matched_fields=match_fields,
                        identified_at=datetime.utcnow(),
                    )
                )

        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        return DeduplicationResult(
            total_records=len(data),
            unique_records=len(data) - total_duplicates,
            duplicate_groups=len(duplicate_groups),
            records_removed=total_duplicates,
            duplicate_groups_list=duplicate_groups,
            processing_time_ms=processing_time,
            processed_at=end_time,
        )

    def _calculate_similarity(
        self, record1: Dict[str, Any], record2: Dict[str, Any], fields: List[str]
    ) -> Decimal:
        if not fields:
            return Decimal("0")

        total_score = Decimal("0")
        for field_name in fields:
            val1 = str(record1.get(field_name, "")).lower().strip()
            val2 = str(record2.get(field_name, "")).lower().strip()

            if val1 == val2:
                total_score += Decimal("1")
            else:
                total_score += self._levenshtein_similarity(val1, val2)

        return total_score / Decimal(str(len(fields)))

    def _levenshtein_similarity(self, s1: str, s2: str) -> Decimal:
        if not s1 and not s2:
            return Decimal("1")
        if not s1 or not s2:
            return Decimal("0")

        if len(s1) < len(s2):
            s1, s2 = s2, s1

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return Decimal(str(round(1 - (distance / max_len), 4)))

    def _select_primary_record(
        self, records: List[Dict[str, Any]], id_field: str
    ) -> Dict[str, Any]:
        best_record = records[0]
        best_score = self._calculate_completeness_score(best_record)

        for record in records[1:]:
            score = self._calculate_completeness_score(record)
            if score > best_score:
                best_score = score
                best_record = record

        return best_record

    def _calculate_completeness_score(self, record: Dict[str, Any]) -> int:
        score = 0
        for key, value in record.items():
            if value is not None and value != "":
                score += 1
        return score

    def merge_duplicate_records(
        self,
        duplicate_group: DuplicateGroup,
        survivorship_rules: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        rules = survivorship_rules or self._survivorship_rules
        all_records = [duplicate_group.primary_record] + duplicate_group.duplicate_records
        merged = {}

        all_fields = set()
        for record in all_records:
            all_fields.update(record.keys())

        for field_name in all_fields:
            rule = rules.get(field_name, "most_complete")
            merged[field_name] = self._apply_survivorship_rule(all_records, field_name, rule)

        return merged

    def _apply_survivorship_rule(
        self, records: List[Dict[str, Any]], field_name: str, rule: str
    ) -> Any:
        values = [r.get(field_name) for r in records if r.get(field_name) is not None]

        if not values:
            return None

        if rule == "first":
            return values[0]
        elif rule == "last":
            return values[-1]
        elif rule == "most_complete":
            return max(values, key=lambda v: len(str(v)) if v else 0)
        elif rule == "most_frequent":
            from collections import Counter
            counter = Counter(str(v) for v in values)
            return counter.most_common(1)[0][0] if counter else None
        elif rule == "max":
            try:
                return max(float(v) for v in values if v is not None)
            except (ValueError, TypeError):
                return values[0]
        elif rule == "min":
            try:
                return min(float(v) for v in values if v is not None)
            except (ValueError, TypeError):
                return values[0]
        else:
            return values[0]

    def remove_duplicates(
        self,
        data: List[Dict[str, Any]],
        key_fields: List[str],
        id_field: str = "id",
    ) -> List[Dict[str, Any]]:
        result = self.find_exact_duplicates(data, key_fields, id_field)
        duplicate_ids = set()

        for group in result.duplicate_groups_list:
            for dup in group.duplicate_records:
                duplicate_ids.add(str(dup.get(id_field)))

        return [r for r in data if str(r.get(id_field)) not in duplicate_ids]

    def set_survivorship_rules(self, rules: Dict[str, str]) -> None:
        self._survivorship_rules = rules

    def set_threshold(self, threshold: Decimal) -> None:
        self._default_threshold = threshold


data_deduplication_utilities = DataDeduplicationUtilities()
