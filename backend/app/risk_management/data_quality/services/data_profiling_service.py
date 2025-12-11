"""Data Profiling Service"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from ..models.data_profiling_models import (
    DataProfile, ColumnProfile, DataDistribution, DataRelationship,
    ProfilingJob, DataAnomaly
)
from ..repositories.data_profiling_repository import data_profiling_repository


class DataProfilingService:
    def __init__(self):
        self.repository = data_profiling_repository

    async def create_profile(
        self, table_name: str, schema_name: str, database_name: str,
        row_count: int, column_count: int, owner: str, profiled_by: str,
        classification: str = "", sensitivity_level: str = "internal"
    ) -> DataProfile:
        profile = DataProfile(
            table_name=table_name, schema_name=schema_name, database_name=database_name,
            row_count=row_count, column_count=column_count, owner=owner,
            profiled_by=profiled_by, classification=classification,
            sensitivity_level=sensitivity_level
        )
        await self.repository.save_profile(profile)
        return profile

    async def add_column_profile(
        self, profile_id: UUID, column_name: str, data_type: str,
        total_values: int, null_count: int, distinct_count: int,
        nullable: bool = True, primary_key: bool = False
    ) -> ColumnProfile:
        null_pct = Decimal(str(null_count / total_values * 100)) if total_values > 0 else Decimal("0")
        distinct_pct = Decimal(str(distinct_count / total_values * 100)) if total_values > 0 else Decimal("0")

        quality_score = Decimal("100") - null_pct
        if distinct_pct < Decimal("1") and not primary_key:
            quality_score -= Decimal("10")

        column = ColumnProfile(
            profile_id=profile_id, column_name=column_name, data_type=data_type,
            nullable=nullable, primary_key=primary_key, total_values=total_values,
            null_count=null_count, null_percentage=null_pct,
            distinct_count=distinct_count, distinct_percentage=distinct_pct,
            data_quality_score=max(quality_score, Decimal("0"))
        )
        await self.repository.save_column_profile(column)
        return column

    async def record_distribution(
        self, profile_id: UUID, column_name: str, distribution_type: str,
        buckets: List[Dict[str, Any]], percentiles: Dict[str, Decimal] = None
    ) -> DataDistribution:
        distribution = DataDistribution(
            profile_id=profile_id, column_name=column_name,
            distribution_type=distribution_type, buckets=buckets,
            percentiles=percentiles or {}
        )
        await self.repository.save_distribution(distribution)
        return distribution

    async def discover_relationship(
        self, source_table: str, source_column: str, target_table: str,
        target_column: str, relationship_type: str, orphan_records: int = 0
    ) -> DataRelationship:
        relationship = DataRelationship(
            source_table=source_table, source_column=source_column,
            target_table=target_table, target_column=target_column,
            relationship_type=relationship_type, orphan_records=orphan_records,
            referential_integrity=orphan_records == 0
        )
        await self.repository.save_relationship(relationship)
        return relationship

    async def create_profiling_job(
        self, job_name: str, job_type: str, target_tables: List[str],
        created_by: str, sample_percentage: Decimal = Decimal("100")
    ) -> ProfilingJob:
        job = ProfilingJob(
            job_name=job_name, job_type=job_type, target_tables=target_tables,
            sample_percentage=sample_percentage, created_by=created_by
        )
        await self.repository.save_job(job)
        return job

    async def complete_job(
        self, job_id: UUID, records_profiled: int, columns_profiled: int, errors: List[str] = None
    ) -> Optional[ProfilingJob]:
        job = await self.repository.find_job_by_id(job_id)
        if job:
            job.status = "completed" if not errors else "completed_with_errors"
            job.completed_at = datetime.utcnow()
            job.records_profiled = records_profiled
            job.columns_profiled = columns_profiled
            job.errors = errors or []
        return job

    async def detect_anomaly(
        self, profile_id: UUID, column_name: str, anomaly_type: str,
        description: str, severity: str, affected_records: int, sample_values: List[str]
    ) -> DataAnomaly:
        anomaly = DataAnomaly(
            profile_id=profile_id, column_name=column_name, anomaly_type=anomaly_type,
            description=description, severity=severity, affected_records=affected_records,
            sample_values=sample_values
        )
        await self.repository.save_anomaly(anomaly)
        return anomaly

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


data_profiling_service = DataProfilingService()
