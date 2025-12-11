"""Data Profiling Repository"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.data_profiling_models import (
    DataProfile, ColumnProfile, DataDistribution, DataRelationship,
    ProfilingJob, DataAnomaly, DataPattern, DataStatistic
)


class DataProfilingRepository:
    def __init__(self):
        self._profiles: Dict[UUID, DataProfile] = {}
        self._column_profiles: Dict[UUID, ColumnProfile] = {}
        self._distributions: Dict[UUID, DataDistribution] = {}
        self._relationships: Dict[UUID, DataRelationship] = {}
        self._jobs: Dict[UUID, ProfilingJob] = {}
        self._anomalies: Dict[UUID, DataAnomaly] = {}
        self._patterns: Dict[UUID, DataPattern] = {}
        self._statistics: Dict[UUID, DataStatistic] = {}

    async def save_profile(self, profile: DataProfile) -> DataProfile:
        self._profiles[profile.profile_id] = profile
        return profile

    async def find_profile_by_id(self, profile_id: UUID) -> Optional[DataProfile]:
        return self._profiles.get(profile_id)

    async def find_all_profiles(self) -> List[DataProfile]:
        return list(self._profiles.values())

    async def find_profiles_by_dataset(self, dataset: str) -> List[DataProfile]:
        return [p for p in self._profiles.values() if p.dataset_name == dataset]

    async def delete_profile(self, profile_id: UUID) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return True
        return False

    async def save_column_profile(self, column_profile: ColumnProfile) -> ColumnProfile:
        self._column_profiles[column_profile.column_profile_id] = column_profile
        return column_profile

    async def find_column_profile_by_id(self, column_profile_id: UUID) -> Optional[ColumnProfile]:
        return self._column_profiles.get(column_profile_id)

    async def find_all_column_profiles(self) -> List[ColumnProfile]:
        return list(self._column_profiles.values())

    async def find_column_profiles_by_profile(self, profile_id: UUID) -> List[ColumnProfile]:
        return [cp for cp in self._column_profiles.values() if cp.profile_id == profile_id]

    async def save_distribution(self, distribution: DataDistribution) -> DataDistribution:
        self._distributions[distribution.distribution_id] = distribution
        return distribution

    async def find_distribution_by_id(self, distribution_id: UUID) -> Optional[DataDistribution]:
        return self._distributions.get(distribution_id)

    async def find_all_distributions(self) -> List[DataDistribution]:
        return list(self._distributions.values())

    async def find_distributions_by_column(self, column_profile_id: UUID) -> List[DataDistribution]:
        return [d for d in self._distributions.values() if d.column_profile_id == column_profile_id]

    async def save_relationship(self, relationship: DataRelationship) -> DataRelationship:
        self._relationships[relationship.relationship_id] = relationship
        return relationship

    async def find_relationship_by_id(self, relationship_id: UUID) -> Optional[DataRelationship]:
        return self._relationships.get(relationship_id)

    async def find_all_relationships(self) -> List[DataRelationship]:
        return list(self._relationships.values())

    async def find_relationships_by_profile(self, profile_id: UUID) -> List[DataRelationship]:
        return [r for r in self._relationships.values() if r.profile_id == profile_id]

    async def save_job(self, job: ProfilingJob) -> ProfilingJob:
        self._jobs[job.job_id] = job
        return job

    async def find_job_by_id(self, job_id: UUID) -> Optional[ProfilingJob]:
        return self._jobs.get(job_id)

    async def find_all_jobs(self) -> List[ProfilingJob]:
        return list(self._jobs.values())

    async def find_jobs_by_status(self, status: str) -> List[ProfilingJob]:
        return [j for j in self._jobs.values() if j.status == status]

    async def find_running_jobs(self) -> List[ProfilingJob]:
        return [j for j in self._jobs.values() if j.status == "running"]

    async def save_anomaly(self, anomaly: DataAnomaly) -> DataAnomaly:
        self._anomalies[anomaly.anomaly_id] = anomaly
        return anomaly

    async def find_anomaly_by_id(self, anomaly_id: UUID) -> Optional[DataAnomaly]:
        return self._anomalies.get(anomaly_id)

    async def find_all_anomalies(self) -> List[DataAnomaly]:
        return list(self._anomalies.values())

    async def find_anomalies_by_profile(self, profile_id: UUID) -> List[DataAnomaly]:
        return [a for a in self._anomalies.values() if a.profile_id == profile_id]

    async def find_anomalies_by_severity(self, severity: str) -> List[DataAnomaly]:
        return [a for a in self._anomalies.values() if a.severity == severity]

    async def save_pattern(self, pattern: DataPattern) -> DataPattern:
        self._patterns[pattern.pattern_id] = pattern
        return pattern

    async def find_pattern_by_id(self, pattern_id: UUID) -> Optional[DataPattern]:
        return self._patterns.get(pattern_id)

    async def find_all_patterns(self) -> List[DataPattern]:
        return list(self._patterns.values())

    async def find_patterns_by_column(self, column_profile_id: UUID) -> List[DataPattern]:
        return [p for p in self._patterns.values() if p.column_profile_id == column_profile_id]

    async def save_statistic(self, statistic: DataStatistic) -> DataStatistic:
        self._statistics[statistic.statistic_id] = statistic
        return statistic

    async def find_statistic_by_id(self, statistic_id: UUID) -> Optional[DataStatistic]:
        return self._statistics.get(statistic_id)

    async def find_all_statistics(self) -> List[DataStatistic]:
        return list(self._statistics.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_profiles": len(self._profiles),
            "total_column_profiles": len(self._column_profiles),
            "total_distributions": len(self._distributions),
            "total_relationships": len(self._relationships),
            "running_jobs": len([j for j in self._jobs.values() if j.status == "running"]),
            "completed_jobs": len([j for j in self._jobs.values() if j.status == "completed"]),
            "total_anomalies": len(self._anomalies),
            "high_severity_anomalies": len([a for a in self._anomalies.values() if a.severity == "high"]),
            "total_patterns": len(self._patterns),
            "total_statistics": len(self._statistics),
        }


data_profiling_repository = DataProfilingRepository()
