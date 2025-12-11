"""Data Enrichment Utilities"""

from typing import List, Dict, Any, Optional, Callable
from decimal import Decimal
from datetime import datetime, date
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class EnrichmentResult:
    record_id: str
    original_fields: int
    enriched_fields: int
    added_fields: List[str]
    enrichment_source: str
    enriched_at: datetime


class DataEnrichmentUtilities:
    def __init__(self):
        self._enrichment_sources: Dict[str, Callable] = {}
        self._lookup_tables: Dict[str, Dict[str, Any]] = {}

    def register_lookup_table(self, table_name: str, data: Dict[str, Any]) -> None:
        self._lookup_tables[table_name] = data

    def register_enrichment_source(self, source_name: str, enrichment_func: Callable) -> None:
        self._enrichment_sources[source_name] = enrichment_func

    def enrich_with_lookup(
        self,
        record: Dict[str, Any],
        lookup_table_name: str,
        lookup_key_field: str,
        fields_to_add: List[str],
        prefix: str = "",
    ) -> Dict[str, Any]:
        enriched = record.copy()
        lookup_table = self._lookup_tables.get(lookup_table_name, {})

        key_value = record.get(lookup_key_field)
        if key_value and key_value in lookup_table:
            lookup_data = lookup_table[key_value]
            for field in fields_to_add:
                if field in lookup_data:
                    new_field_name = f"{prefix}{field}" if prefix else field
                    enriched[new_field_name] = lookup_data[field]

        return enriched

    def enrich_with_calculated_fields(
        self,
        record: Dict[str, Any],
        calculations: Dict[str, Callable],
    ) -> Dict[str, Any]:
        enriched = record.copy()

        for field_name, calculation in calculations.items():
            try:
                enriched[field_name] = calculation(record)
            except Exception:
                enriched[field_name] = None

        return enriched

    def enrich_with_derived_fields(
        self,
        record: Dict[str, Any],
        derivations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        enriched = record.copy()

        for derivation in derivations:
            source_field = derivation.get("source_field")
            target_field = derivation.get("target_field")
            derivation_type = derivation.get("type")

            source_value = record.get(source_field)

            if derivation_type == "extract_year":
                if isinstance(source_value, (datetime, date)):
                    enriched[target_field] = source_value.year
                elif isinstance(source_value, str):
                    try:
                        dt = datetime.fromisoformat(source_value)
                        enriched[target_field] = dt.year
                    except ValueError:
                        enriched[target_field] = None

            elif derivation_type == "extract_month":
                if isinstance(source_value, (datetime, date)):
                    enriched[target_field] = source_value.month
                elif isinstance(source_value, str):
                    try:
                        dt = datetime.fromisoformat(source_value)
                        enriched[target_field] = dt.month
                    except ValueError:
                        enriched[target_field] = None

            elif derivation_type == "age_from_birthdate":
                if source_value:
                    try:
                        if isinstance(source_value, str):
                            birth_date = datetime.fromisoformat(source_value).date()
                        elif isinstance(source_value, datetime):
                            birth_date = source_value.date()
                        elif isinstance(source_value, date):
                            birth_date = source_value
                        else:
                            enriched[target_field] = None
                            continue

                        today = date.today()
                        age = today.year - birth_date.year
                        if today.month < birth_date.month or (
                            today.month == birth_date.month and today.day < birth_date.day
                        ):
                            age -= 1
                        enriched[target_field] = age
                    except Exception:
                        enriched[target_field] = None

            elif derivation_type == "concat":
                fields_to_concat = derivation.get("fields", [])
                separator = derivation.get("separator", " ")
                values = [str(record.get(f, "")) for f in fields_to_concat if record.get(f)]
                enriched[target_field] = separator.join(values)

            elif derivation_type == "uppercase":
                if isinstance(source_value, str):
                    enriched[target_field] = source_value.upper()

            elif derivation_type == "lowercase":
                if isinstance(source_value, str):
                    enriched[target_field] = source_value.lower()

            elif derivation_type == "length":
                if source_value is not None:
                    enriched[target_field] = len(str(source_value))

            elif derivation_type == "is_null":
                enriched[target_field] = source_value is None

            elif derivation_type == "is_not_null":
                enriched[target_field] = source_value is not None

        return enriched

    def add_metadata_fields(
        self,
        record: Dict[str, Any],
        source_system: str = "",
        batch_id: str = "",
    ) -> Dict[str, Any]:
        enriched = record.copy()
        enriched["_record_id"] = str(uuid4())
        enriched["_ingestion_timestamp"] = datetime.utcnow().isoformat()
        enriched["_source_system"] = source_system
        enriched["_batch_id"] = batch_id
        enriched["_version"] = 1
        return enriched

    def enrich_dataset(
        self,
        data: List[Dict[str, Any]],
        enrichment_configs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        enriched_data = []

        for record in data:
            enriched_record = record.copy()

            for config in enrichment_configs:
                enrichment_type = config.get("type")

                if enrichment_type == "lookup":
                    enriched_record = self.enrich_with_lookup(
                        enriched_record,
                        config.get("lookup_table"),
                        config.get("key_field"),
                        config.get("fields"),
                        config.get("prefix", ""),
                    )

                elif enrichment_type == "derived":
                    enriched_record = self.enrich_with_derived_fields(
                        enriched_record,
                        config.get("derivations", []),
                    )

                elif enrichment_type == "metadata":
                    enriched_record = self.add_metadata_fields(
                        enriched_record,
                        config.get("source_system", ""),
                        config.get("batch_id", ""),
                    )

            enriched_data.append(enriched_record)

        return enriched_data

    def get_lookup_tables(self) -> List[str]:
        return list(self._lookup_tables.keys())

    def get_enrichment_sources(self) -> List[str]:
        return list(self._enrichment_sources.keys())


data_enrichment_utilities = DataEnrichmentUtilities()
