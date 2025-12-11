"""Data Timeliness Analysis Utilities"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class TimelinessRule:
    rule_id: str
    rule_name: str
    date_field: str
    max_age_days: int
    freshness_level: str
    parameters: Dict[str, Any]


@dataclass
class StaleRecord:
    record_id: str
    date_field: str
    record_date: datetime
    age_days: int
    staleness_level: str


@dataclass
class TimelinessCheckResult:
    check_id: str
    rule: TimelinessRule
    total_records: int
    fresh_records: int
    stale_records: int
    timeliness_rate: Decimal
    average_age_days: Decimal
    stale_record_details: List[StaleRecord]
    checked_at: datetime


class DataTimelinessUtilities:
    def __init__(self):
        self._rules: Dict[str, TimelinessRule] = {}
        self._freshness_thresholds = {
            "real_time": 0,
            "near_real_time": 1,
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90,
            "annual": 365,
        }

    def create_rule(
        self,
        rule_name: str,
        date_field: str,
        max_age_days: int,
        freshness_level: str = "daily",
        parameters: Dict[str, Any] = None,
    ) -> TimelinessRule:
        rule = TimelinessRule(
            rule_id=str(uuid4()),
            rule_name=rule_name,
            date_field=date_field,
            max_age_days=max_age_days,
            freshness_level=freshness_level,
            parameters=parameters or {},
        )
        self._rules[rule.rule_id] = rule
        return rule

    def check_timeliness(
        self,
        data: List[Dict[str, Any]],
        rule: TimelinessRule,
        id_field: str = "id",
        reference_date: datetime = None,
    ) -> TimelinessCheckResult:
        reference = reference_date or datetime.utcnow()
        if isinstance(reference, datetime):
            reference = reference.date() if hasattr(reference, 'date') else reference

        stale_records = []
        fresh_count = 0
        total_age = 0
        valid_count = 0

        for i, record in enumerate(data):
            record_id = str(record.get(id_field, i))
            date_value = record.get(rule.date_field)

            if date_value is None:
                continue

            record_date = self._parse_date(date_value)
            if record_date is None:
                continue

            valid_count += 1
            age_days = (reference - record_date).days if isinstance(reference, date) else 0
            total_age += age_days

            if age_days <= rule.max_age_days:
                fresh_count += 1
            else:
                staleness = self._determine_staleness_level(age_days, rule.max_age_days)
                stale_records.append(
                    StaleRecord(
                        record_id=record_id,
                        date_field=rule.date_field,
                        record_date=datetime.combine(record_date, datetime.min.time()),
                        age_days=age_days,
                        staleness_level=staleness,
                    )
                )

        total = len(data)
        timeliness_rate = Decimal(str(fresh_count / total * 100)) if total > 0 else Decimal("100")
        avg_age = Decimal(str(total_age / valid_count)) if valid_count > 0 else Decimal("0")

        return TimelinessCheckResult(
            check_id=str(uuid4()),
            rule=rule,
            total_records=total,
            fresh_records=fresh_count,
            stale_records=len(stale_records),
            timeliness_rate=timeliness_rate,
            average_age_days=avg_age,
            stale_record_details=stale_records,
            checked_at=datetime.utcnow(),
        )

    def _parse_date(self, value: Any) -> Optional[date]:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value[:19], fmt[:len(value)]).date()
                except ValueError:
                    continue
        return None

    def _determine_staleness_level(self, age_days: int, max_age: int) -> str:
        excess = age_days - max_age
        if excess <= max_age:
            return "slightly_stale"
        elif excess <= max_age * 3:
            return "moderately_stale"
        elif excess <= max_age * 7:
            return "very_stale"
        else:
            return "critically_stale"

    def calculate_data_currency(
        self,
        data: List[Dict[str, Any]],
        date_field: str,
        reference_date: datetime = None,
    ) -> Dict[str, Any]:
        reference = reference_date or datetime.utcnow()
        if isinstance(reference, datetime):
            reference = reference.date()

        ages = []
        for record in data:
            date_value = record.get(date_field)
            record_date = self._parse_date(date_value)
            if record_date:
                age = (reference - record_date).days
                ages.append(age)

        if not ages:
            return {
                "total_records": len(data),
                "records_with_dates": 0,
                "min_age_days": None,
                "max_age_days": None,
                "avg_age_days": None,
                "median_age_days": None,
            }

        sorted_ages = sorted(ages)
        median_idx = len(sorted_ages) // 2
        median = sorted_ages[median_idx]

        return {
            "total_records": len(data),
            "records_with_dates": len(ages),
            "min_age_days": min(ages),
            "max_age_days": max(ages),
            "avg_age_days": round(sum(ages) / len(ages), 2),
            "median_age_days": median,
        }

    def get_freshness_distribution(
        self,
        data: List[Dict[str, Any]],
        date_field: str,
        reference_date: datetime = None,
    ) -> Dict[str, int]:
        reference = reference_date or datetime.utcnow()
        if isinstance(reference, datetime):
            reference = reference.date()

        distribution = {
            "today": 0,
            "yesterday": 0,
            "last_7_days": 0,
            "last_30_days": 0,
            "last_90_days": 0,
            "older": 0,
            "unknown": 0,
        }

        for record in data:
            date_value = record.get(date_field)
            record_date = self._parse_date(date_value)

            if record_date is None:
                distribution["unknown"] += 1
                continue

            age = (reference - record_date).days

            if age == 0:
                distribution["today"] += 1
            elif age == 1:
                distribution["yesterday"] += 1
            elif age <= 7:
                distribution["last_7_days"] += 1
            elif age <= 30:
                distribution["last_30_days"] += 1
            elif age <= 90:
                distribution["last_90_days"] += 1
            else:
                distribution["older"] += 1

        return distribution

    def set_freshness_threshold(self, level: str, days: int) -> None:
        self._freshness_thresholds[level] = days

    def get_freshness_thresholds(self) -> Dict[str, int]:
        return self._freshness_thresholds.copy()

    def get_rules(self) -> Dict[str, TimelinessRule]:
        return self._rules.copy()


data_timeliness_utilities = DataTimelinessUtilities()
