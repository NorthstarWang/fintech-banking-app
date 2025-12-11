"""Data Profiling Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel, Field


class DataProfile(BaseModel):
    profile_id: UUID = Field(default_factory=uuid4)
    table_name: str
    schema_name: str
    database_name: str
    profile_date: datetime = Field(default_factory=datetime.utcnow)
    row_count: int = 0
    column_count: int = 0
    size_bytes: int = 0
    last_updated: Optional[datetime] = None
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
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    avg_value: Optional[Decimal] = None
    std_dev: Optional[Decimal] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[Decimal] = None
    pattern_analysis: Dict[str, int] = Field(default_factory=dict)
    top_values: List[Dict[str, Any]] = Field(default_factory=list)
    data_quality_score: Decimal = Decimal("100")


class DataDistribution(BaseModel):
    distribution_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    column_name: str
    distribution_type: str  # histogram, frequency, percentile
    distribution_date: datetime = Field(default_factory=datetime.utcnow)
    buckets: List[Dict[str, Any]] = Field(default_factory=list)
    percentiles: Dict[str, Decimal] = Field(default_factory=dict)
    skewness: Optional[Decimal] = None
    kurtosis: Optional[Decimal] = None


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
    discovered_date: datetime = Field(default_factory=datetime.utcnow)
    validated: bool = False
    validated_by: Optional[str] = None


class ProfilingJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    job_name: str
    job_type: str  # full, incremental, sample
    target_tables: List[str] = Field(default_factory=list)
    schedule: str = ""
    sample_percentage: Decimal = Decimal("100")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    records_profiled: int = 0
    columns_profiled: int = 0
    errors: List[str] = Field(default_factory=list)
    created_by: str = ""


class DataAnomaly(BaseModel):
    anomaly_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    column_name: str
    anomaly_type: str
    description: str
    detected_date: datetime = Field(default_factory=datetime.utcnow)
    severity: str = "medium"
    affected_records: int = 0
    sample_values: List[str] = Field(default_factory=list)
    expected_pattern: str = ""
    actual_pattern: str = ""
    status: str = "detected"
    acknowledged_by: Optional[str] = None
