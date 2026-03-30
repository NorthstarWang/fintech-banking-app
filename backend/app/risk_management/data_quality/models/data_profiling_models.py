"""Data Profiling Models"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DataProfile(BaseModel):
    profile_id: UUID = Field(default_factory=uuid4)
    table_name: str
    schema_name: str
    database_name: str
    profile_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    row_count: int = 0
    column_count: int = 0
    size_bytes: int = 0
    last_updated: datetime | None = None
    update_frequency: str = ""
    owner: str = ""
    classification: str = ""
    sensitivity_level: str = "internal"
    retention_period: str = ""
    profiled_by: str = ""


class ColumnProfile(BaseModel):
    column_profile_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    column_name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: bool = False
    unique_constraint: bool = False
    total_values: int = 0
    null_count: int = 0
    null_percentage: Decimal = Decimal("0")
    distinct_count: int = 0
    distinct_percentage: Decimal = Decimal("0")
    min_value: str | None = None
    max_value: str | None = None
    avg_value: Decimal | None = None
    std_dev: Decimal | None = None
    min_length: int | None = None
    max_length: int | None = None
    avg_length: Decimal | None = None
    pattern_analysis: dict[str, int] = Field(default_factory=dict)
    top_values: list[dict[str, Any]] = Field(default_factory=list)
    data_quality_score: Decimal = Decimal("100")


class DataDistribution(BaseModel):
    distribution_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    column_name: str
    distribution_type: str  # histogram, frequency, percentile
    distribution_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    buckets: list[dict[str, Any]] = Field(default_factory=list)
    percentiles: dict[str, Decimal] = Field(default_factory=dict)
    skewness: Decimal | None = None
    kurtosis: Decimal | None = None


class DataRelationship(BaseModel):
    relationship_id: UUID = Field(default_factory=uuid4)
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str  # one_to_one, one_to_many, many_to_many
    cardinality: str = ""
    referential_integrity: bool = True
    orphan_records: int = 0
    discovered_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    validated: bool = False
    validated_by: str | None = None


class ProfilingJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    job_name: str
    job_type: str  # full, incremental, sample
    target_tables: list[str] = Field(default_factory=list)
    schedule: str = ""
    sample_percentage: Decimal = Decimal("100")
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"
    records_profiled: int = 0
    columns_profiled: int = 0
    errors: list[str] = Field(default_factory=list)
    created_by: str = ""


class DataAnomaly(BaseModel):
    anomaly_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    column_name: str
    anomaly_type: str
    description: str
    detected_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: str = "medium"
    affected_records: int = 0
    sample_values: list[str] = Field(default_factory=list)
    expected_pattern: str = ""
    actual_pattern: str = ""
    status: str = "detected"
    acknowledged_by: str | None = None
