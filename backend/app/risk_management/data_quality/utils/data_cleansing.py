"""Data Cleansing Utilities"""

from typing import List, Dict, Any, Optional, Callable
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
import re


@dataclass
class CleansingResult:
    original_value: Any
    cleansed_value: Any
    transformations_applied: List[str]
    was_modified: bool


class DataCleansingUtilities:
    def __init__(self):
        self._transformations: Dict[str, Callable] = {}
        self._register_default_transformations()

    def _register_default_transformations(self) -> None:
        self._transformations["trim"] = self._trim_whitespace
        self._transformations["uppercase"] = self._to_uppercase
        self._transformations["lowercase"] = self._to_lowercase
        self._transformations["titlecase"] = self._to_titlecase
        self._transformations["remove_special_chars"] = self._remove_special_chars
        self._transformations["normalize_whitespace"] = self._normalize_whitespace
        self._transformations["remove_digits"] = self._remove_digits
        self._transformations["extract_digits"] = self._extract_digits
        self._transformations["normalize_phone"] = self._normalize_phone
        self._transformations["normalize_email"] = self._normalize_email
        self._transformations["standardize_date"] = self._standardize_date
        self._transformations["remove_null_chars"] = self._remove_null_chars

    def cleanse_value(
        self, value: Any, transformations: List[str]
    ) -> CleansingResult:
        original = value
        current_value = value
        applied = []

        for transform_name in transformations:
            transform_func = self._transformations.get(transform_name)
            if transform_func:
                new_value = transform_func(current_value)
                if new_value != current_value:
                    applied.append(transform_name)
                    current_value = new_value

        return CleansingResult(
            original_value=original,
            cleansed_value=current_value,
            transformations_applied=applied,
            was_modified=original != current_value,
        )

    def cleanse_record(
        self, record: Dict[str, Any], field_transformations: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        cleansed = record.copy()

        for field_name, transformations in field_transformations.items():
            if field_name in cleansed:
                result = self.cleanse_value(cleansed[field_name], transformations)
                cleansed[field_name] = result.cleansed_value

        return cleansed

    def cleanse_dataset(
        self, data: List[Dict[str, Any]], field_transformations: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        return [self.cleanse_record(record, field_transformations) for record in data]

    def _trim_whitespace(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    def _to_uppercase(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.upper()
        return value

    def _to_lowercase(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.lower()
        return value

    def _to_titlecase(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.title()
        return value

    def _remove_special_chars(self, value: Any) -> Any:
        if isinstance(value, str):
            return re.sub(r"[^a-zA-Z0-9\s]", "", value)
        return value

    def _normalize_whitespace(self, value: Any) -> Any:
        if isinstance(value, str):
            return re.sub(r"\s+", " ", value).strip()
        return value

    def _remove_digits(self, value: Any) -> Any:
        if isinstance(value, str):
            return re.sub(r"\d", "", value)
        return value

    def _extract_digits(self, value: Any) -> Any:
        if isinstance(value, str):
            return re.sub(r"\D", "", value)
        return value

    def _normalize_phone(self, value: Any) -> Any:
        if isinstance(value, str):
            digits = re.sub(r"\D", "", value)
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == "1":
                digits = digits[1:]
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return value

    def _normalize_email(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.lower().strip()
        return value

    def _standardize_date(self, value: Any) -> Any:
        if isinstance(value, str):
            date_formats = [
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y/%m/%d",
                "%m-%d-%Y",
                "%d-%m-%Y",
                "%Y%m%d",
            ]
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return value

    def _remove_null_chars(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.replace("\x00", "")
        return value

    def register_transformation(self, name: str, func: Callable) -> None:
        self._transformations[name] = func

    def get_available_transformations(self) -> List[str]:
        return list(self._transformations.keys())


data_cleansing_utilities = DataCleansingUtilities()
