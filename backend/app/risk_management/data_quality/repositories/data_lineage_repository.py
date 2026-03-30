"""Data Lineage Repository"""

from typing import Any
from uuid import UUID

from ..models.data_lineage_models import (
    ColumnLineage,
    DataAsset,
    DataFlow,
    DataPipeline,
    DataTransformation,
    ImpactAnalysis,
    LineageSnapshot,
)


class DataLineageRepository:
    def __init__(self):
        self._assets: dict[UUID, DataAsset] = {}
        self._flows: dict[UUID, DataFlow] = {}
        self._column_lineages: dict[UUID, ColumnLineage] = {}
        self._pipelines: dict[UUID, DataPipeline] = {}
        self._impact_analyses: dict[UUID, ImpactAnalysis] = {}
        self._snapshots: dict[UUID, LineageSnapshot] = {}
        self._transformations: dict[UUID, DataTransformation] = {}

    async def save_asset(self, asset: DataAsset) -> DataAsset:
        self._assets[asset.asset_id] = asset
        return asset

    async def find_asset_by_id(self, asset_id: UUID) -> DataAsset | None:
        return self._assets.get(asset_id)

    async def find_all_assets(self) -> list[DataAsset]:
        return list(self._assets.values())

    async def find_assets_by_type(self, asset_type: str) -> list[DataAsset]:
        return [a for a in self._assets.values() if a.asset_type == asset_type]

    async def find_assets_by_database(self, database: str) -> list[DataAsset]:
        return [a for a in self._assets.values() if a.database == database]

    async def delete_asset(self, asset_id: UUID) -> bool:
        if asset_id in self._assets:
            del self._assets[asset_id]
            return True
        return False

    async def save_flow(self, flow: DataFlow) -> DataFlow:
        self._flows[flow.flow_id] = flow
        return flow

    async def find_flow_by_id(self, flow_id: UUID) -> DataFlow | None:
        return self._flows.get(flow_id)

    async def find_all_flows(self) -> list[DataFlow]:
        return list(self._flows.values())

    async def find_flows_by_source(self, source_asset_id: UUID) -> list[DataFlow]:
        return [f for f in self._flows.values() if f.source_asset_id == source_asset_id]

    async def find_flows_by_target(self, target_asset_id: UUID) -> list[DataFlow]:
        return [f for f in self._flows.values() if f.target_asset_id == target_asset_id]

    async def delete_flow(self, flow_id: UUID) -> bool:
        if flow_id in self._flows:
            del self._flows[flow_id]
            return True
        return False

    async def save_column_lineage(self, lineage: ColumnLineage) -> ColumnLineage:
        self._column_lineages[lineage.lineage_id] = lineage
        return lineage

    async def find_column_lineage_by_id(self, lineage_id: UUID) -> ColumnLineage | None:
        return self._column_lineages.get(lineage_id)

    async def find_all_column_lineages(self) -> list[ColumnLineage]:
        return list(self._column_lineages.values())

    async def find_column_lineages_by_flow(self, flow_id: UUID) -> list[ColumnLineage]:
        return [cl for cl in self._column_lineages.values() if cl.flow_id == flow_id]

    async def find_column_lineages_by_source(self, source_table: str, source_column: str) -> list[ColumnLineage]:
        return [
            cl for cl in self._column_lineages.values()
            if cl.source_table == source_table and cl.source_column == source_column
        ]

    async def save_pipeline(self, pipeline: DataPipeline) -> DataPipeline:
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    async def find_pipeline_by_id(self, pipeline_id: UUID) -> DataPipeline | None:
        return self._pipelines.get(pipeline_id)

    async def find_all_pipelines(self) -> list[DataPipeline]:
        return list(self._pipelines.values())

    async def find_pipelines_by_type(self, pipeline_type: str) -> list[DataPipeline]:
        return [p for p in self._pipelines.values() if p.pipeline_type == pipeline_type]

    async def find_active_pipelines(self) -> list[DataPipeline]:
        return [p for p in self._pipelines.values() if p.is_active]

    async def save_impact_analysis(self, analysis: ImpactAnalysis) -> ImpactAnalysis:
        self._impact_analyses[analysis.analysis_id] = analysis
        return analysis

    async def find_impact_analysis_by_id(self, analysis_id: UUID) -> ImpactAnalysis | None:
        return self._impact_analyses.get(analysis_id)

    async def find_all_impact_analyses(self) -> list[ImpactAnalysis]:
        return list(self._impact_analyses.values())

    async def find_impact_analyses_by_asset(self, asset_id: UUID) -> list[ImpactAnalysis]:
        return [ia for ia in self._impact_analyses.values() if ia.asset_id == asset_id]

    async def save_snapshot(self, snapshot: LineageSnapshot) -> LineageSnapshot:
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    async def find_snapshot_by_id(self, snapshot_id: UUID) -> LineageSnapshot | None:
        return self._snapshots.get(snapshot_id)

    async def find_all_snapshots(self) -> list[LineageSnapshot]:
        return list(self._snapshots.values())

    async def find_latest_snapshot(self) -> LineageSnapshot | None:
        snapshots = list(self._snapshots.values())
        if not snapshots:
            return None
        return max(snapshots, key=lambda s: s.created_at)

    async def save_transformation(self, transformation: DataTransformation) -> DataTransformation:
        self._transformations[transformation.transformation_id] = transformation
        return transformation

    async def find_transformation_by_id(self, transformation_id: UUID) -> DataTransformation | None:
        return self._transformations.get(transformation_id)

    async def find_all_transformations(self) -> list[DataTransformation]:
        return list(self._transformations.values())

    async def find_transformations_by_flow(self, flow_id: UUID) -> list[DataTransformation]:
        return [t for t in self._transformations.values() if t.flow_id == flow_id]

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_assets": len(self._assets),
            "total_flows": len(self._flows),
            "total_column_lineages": len(self._column_lineages),
            "total_pipelines": len(self._pipelines),
            "active_pipelines": len([p for p in self._pipelines.values() if p.is_active]),
            "total_impact_analyses": len(self._impact_analyses),
            "total_snapshots": len(self._snapshots),
            "total_transformations": len(self._transformations),
        }


data_lineage_repository = DataLineageRepository()
