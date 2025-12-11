"""Data Profiling Routes"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.data_profiling_service import data_profiling_service

router = APIRouter(prefix="/data-profiling", tags=["Data Profiling"])


class CreateProfileRequest(BaseModel):
    dataset_name: str
    database: str
    schema_name: str
    table_name: str
    profiled_by: str


class AddColumnProfileRequest(BaseModel):
    profile_id: UUID
    column_name: str
    data_type: str
    total_count: int
    null_count: int
    distinct_count: int
    min_value: str = ""
    max_value: str = ""
    avg_value: Optional[Decimal] = None


class RecordDistributionRequest(BaseModel):
    column_profile_id: UUID
    distribution_type: str
    buckets: List[Dict[str, Any]]


class RecordRelationshipRequest(BaseModel):
    profile_id: UUID
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str
    confidence_score: Decimal


class StartProfilingJobRequest(BaseModel):
    job_name: str
    dataset_name: str
    job_type: str
    columns_to_profile: List[str]
    started_by: str


class RecordAnomalyRequest(BaseModel):
    profile_id: UUID
    column_name: str
    anomaly_type: str
    anomaly_description: str
    severity: str
    affected_records: int


class RecordPatternRequest(BaseModel):
    column_profile_id: UUID
    pattern_name: str
    pattern_regex: str
    match_count: int
    match_percentage: Decimal


class RecordStatisticRequest(BaseModel):
    profile_id: UUID
    statistic_name: str
    statistic_type: str
    value: Decimal
    column_name: str = ""


@router.post("/profiles")
async def create_profile(request: CreateProfileRequest):
    profile = await data_profiling_service.create_profile(
        dataset_name=request.dataset_name,
        database=request.database,
        schema_name=request.schema_name,
        table_name=request.table_name,
        profiled_by=request.profiled_by,
    )
    return {"status": "created", "profile_id": str(profile.profile_id)}


@router.get("/profiles")
async def get_all_profiles():
    profiles = await data_profiling_service.repository.find_all_profiles()
    return {"profiles": [{"profile_id": str(p.profile_id), "dataset": p.dataset_name} for p in profiles]}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: UUID):
    profile = await data_profiling_service.repository.find_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/profiles/{profile_id}/complete")
async def complete_profile(profile_id: UUID, row_count: int, column_count: int):
    profile = await data_profiling_service.complete_profile(
        profile_id=profile_id,
        row_count=row_count,
        column_count=column_count,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "completed", "profile_id": str(profile.profile_id)}


@router.post("/column-profiles")
async def add_column_profile(request: AddColumnProfileRequest):
    column_profile = await data_profiling_service.add_column_profile(
        profile_id=request.profile_id,
        column_name=request.column_name,
        data_type=request.data_type,
        total_count=request.total_count,
        null_count=request.null_count,
        distinct_count=request.distinct_count,
        min_value=request.min_value,
        max_value=request.max_value,
        avg_value=request.avg_value,
    )
    return {"status": "created", "column_profile_id": str(column_profile.column_profile_id)}


@router.get("/column-profiles")
async def get_all_column_profiles():
    profiles = await data_profiling_service.repository.find_all_column_profiles()
    return {"column_profiles": [{"id": str(p.column_profile_id), "column": p.column_name} for p in profiles]}


@router.post("/distributions")
async def record_distribution(request: RecordDistributionRequest):
    distribution = await data_profiling_service.record_distribution(
        column_profile_id=request.column_profile_id,
        distribution_type=request.distribution_type,
        buckets=request.buckets,
    )
    return {"status": "recorded", "distribution_id": str(distribution.distribution_id)}


@router.get("/distributions")
async def get_all_distributions():
    distributions = await data_profiling_service.repository.find_all_distributions()
    return {"distributions": [{"id": str(d.distribution_id), "type": d.distribution_type} for d in distributions]}


@router.post("/relationships")
async def record_relationship(request: RecordRelationshipRequest):
    relationship = await data_profiling_service.record_relationship(
        profile_id=request.profile_id,
        source_column=request.source_column,
        target_table=request.target_table,
        target_column=request.target_column,
        relationship_type=request.relationship_type,
        confidence_score=request.confidence_score,
    )
    return {"status": "recorded", "relationship_id": str(relationship.relationship_id)}


@router.get("/relationships")
async def get_all_relationships():
    relationships = await data_profiling_service.repository.find_all_relationships()
    return {"relationships": [{"id": str(r.relationship_id), "type": r.relationship_type} for r in relationships]}


@router.post("/jobs")
async def start_profiling_job(request: StartProfilingJobRequest):
    job = await data_profiling_service.start_profiling_job(
        job_name=request.job_name,
        dataset_name=request.dataset_name,
        job_type=request.job_type,
        columns_to_profile=request.columns_to_profile,
        started_by=request.started_by,
    )
    return {"status": "started", "job_id": str(job.job_id)}


@router.post("/jobs/{job_id}/complete")
async def complete_job(job_id: UUID, records_profiled: int):
    job = await data_profiling_service.complete_job(
        job_id=job_id,
        records_profiled=records_profiled,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "completed", "job_id": str(job.job_id)}


@router.get("/jobs")
async def get_all_jobs():
    jobs = await data_profiling_service.repository.find_all_jobs()
    return {"jobs": [{"job_id": str(j.job_id), "name": j.job_name, "status": j.status} for j in jobs]}


@router.post("/anomalies")
async def record_anomaly(request: RecordAnomalyRequest):
    anomaly = await data_profiling_service.record_anomaly(
        profile_id=request.profile_id,
        column_name=request.column_name,
        anomaly_type=request.anomaly_type,
        anomaly_description=request.anomaly_description,
        severity=request.severity,
        affected_records=request.affected_records,
    )
    return {"status": "recorded", "anomaly_id": str(anomaly.anomaly_id)}


@router.get("/anomalies")
async def get_all_anomalies():
    anomalies = await data_profiling_service.repository.find_all_anomalies()
    return {"anomalies": [{"id": str(a.anomaly_id), "type": a.anomaly_type, "severity": a.severity} for a in anomalies]}


@router.post("/patterns")
async def record_pattern(request: RecordPatternRequest):
    pattern = await data_profiling_service.record_pattern(
        column_profile_id=request.column_profile_id,
        pattern_name=request.pattern_name,
        pattern_regex=request.pattern_regex,
        match_count=request.match_count,
        match_percentage=request.match_percentage,
    )
    return {"status": "recorded", "pattern_id": str(pattern.pattern_id)}


@router.get("/patterns")
async def get_all_patterns():
    patterns = await data_profiling_service.repository.find_all_patterns()
    return {"patterns": [{"id": str(p.pattern_id), "name": p.pattern_name} for p in patterns]}


@router.post("/statistics")
async def record_statistic(request: RecordStatisticRequest):
    statistic = await data_profiling_service.record_statistic(
        profile_id=request.profile_id,
        statistic_name=request.statistic_name,
        statistic_type=request.statistic_type,
        value=request.value,
        column_name=request.column_name,
    )
    return {"status": "recorded", "statistic_id": str(statistic.statistic_id)}


@router.get("/statistics")
async def get_statistics():
    return await data_profiling_service.get_statistics()
