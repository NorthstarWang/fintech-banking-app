"""Data Lineage Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class DataAsset(BaseModel):
    asset_id: UUID = Field(default_factory=uuid4)
    asset_name: str
    asset_type: str  # table, view, file, api, report
    database: str = ""
    schema_name: str = ""
    description: str = ""
    owner: str = ""
    steward: str = ""
    classification: str = ""
    tags: List[str] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class DataFlow(BaseModel):
    flow_id: UUID = Field(default_factory=uuid4)
    flow_name: str
    source_asset_id: UUID
    target_asset_id: UUID
    flow_type: str  # etl, api, manual, streaming
    transformation_type: str = ""
    transformation_logic: str = ""
    schedule: str = ""
    frequency: str = ""
    last_execution: Optional[datetime] = None
    status: str = "active"
    created_by: str = ""


class ColumnLineage(BaseModel):
    lineage_id: UUID = Field(default_factory=uuid4)
    flow_id: UUID
    source_column: str
    source_table: str
    target_column: str
    target_table: str
    transformation: str = ""
    confidence_score: float = 1.0
    discovered_method: str = "manual"  # manual, parsed, inferred
    verified: bool = False
    verified_by: Optional[str] = None


class DataPipeline(BaseModel):
    pipeline_id: UUID = Field(default_factory=uuid4)
    pipeline_name: str
    pipeline_type: str  # batch, streaming, real_time
    description: str = ""
    source_systems: List[str] = Field(default_factory=list)
    target_systems: List[str] = Field(default_factory=list)
    flows: List[UUID] = Field(default_factory=list)
    schedule: str = ""
    owner: str = ""
    status: str = "active"
    created_date: datetime = Field(default_factory=datetime.utcnow)


class ImpactAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    analysis_type: str  # upstream, downstream, full
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    upstream_assets: List[Dict[str, Any]] = Field(default_factory=list)
    downstream_assets: List[Dict[str, Any]] = Field(default_factory=list)
    affected_reports: List[str] = Field(default_factory=list)
    affected_processes: List[str] = Field(default_factory=list)
    risk_assessment: str = ""
    performed_by: str = ""


class LineageSnapshot(BaseModel):
    snapshot_id: UUID = Field(default_factory=uuid4)
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    snapshot_type: str  # scheduled, on_demand, change_triggered
    assets_captured: int = 0
    flows_captured: int = 0
    lineages_captured: int = 0
    changes_detected: int = 0
    status: str = "completed"


class DataTransformation(BaseModel):
    transformation_id: UUID = Field(default_factory=uuid4)
    flow_id: UUID
    transformation_name: str
    transformation_type: str  # mapping, aggregation, filter, join, pivot
    source_columns: List[str] = Field(default_factory=list)
    target_columns: List[str] = Field(default_factory=list)
    logic: str = ""
    sql_expression: str = ""
    business_rule: str = ""
    documented_by: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)
