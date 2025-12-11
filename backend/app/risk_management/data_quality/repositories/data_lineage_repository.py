"""Data Lineage Repository"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.data_lineage_models import (
    DataAsset, DataFlow, ColumnLineage, DataPipeline,
    ImpactAnalysis, LineageSnapshot, DataTransformation
)


class DataLineageRepository:
    def __init__(self):
        self._assets: Dict[UUID, DataAsset] = {}
        self._flows: Dict[UUID, DataFlow] = {}
        self._column_lineages: Dict[UUID, ColumnLineage] = {}
        self._pipelines: Dict[UUID, DataPipeline] = {}
        self._impact_analyses: Dict[UUID, ImpactAnalysis] = {}
        self._snapshots: Dict[UUID, LineageSnapshot] = {}
        self._transformations: Dict[UUID, DataTransformation] = {}

    async def save_asset(self, asset: DataAsset) -> DataAsset:
        self._assets[asset.asset_id] = asset
        return asset

    async def find_asset_by_id(self, asset_id: UUID) -> Optional[DataAsset]:
        return self._assets.get(asset_id)

    async def find_all_assets(self) -> List[DataAsset]:
        return list(self._assets.values())

    async def find_assets_by_type(self, asset_type: str) -> List[DataAsset]:
        return [a for a in self._assets.values() if a.asset_type == asset_type]

    async def find_assets_by_database(self, database: str) -> List[DataAsset]:
        return [a for a in self._assets.values() if a.database == database]

    async def delete_asset(self, asset_id: UUID) -> bool:
        if asset_id in self._assets:
            del self._assets[asset_id]
            return True
        return False

    async def save_flow(self, flow: DataFlow) -> DataFlow:
        self._flows[flow.flow_id] = flow
        return flow

    async def find_flow_by_id(self, flow_id: UUID) -> Optional[DataFlow]:
        return self._flows.get(flow_id)

    async def find_all_flows(self) -> List[DataFlow]:
        return list(self._flows.values())

    async def find_flows_by_source(self, source_asset_id: UUID) -> List[DataFlow]:
        return [f for f in self._flows.values() if f.source_asset_id == source_asset_id]

    async def find_flows_by_target(self, target_asset_id: UUID) -> List[DataFlow]:
        return [f for f in self._flows.values() if f.target_asset_id == target_asset_id]

    async def delete_flow(self, flow_id: UUID) -> bool:
        if flow_id in self._flows:
            del self._flows[flow_id]
            return True
        return False

    async def save_column_lineage(self, lineage: ColumnLineage) -> ColumnLineage:
        self._column_lineages[lineage.lineage_id] = lineage
        return lineage

    async def find_column_lineage_by_id(self, lineage_id: UUID) -> Optional[ColumnLineage]:
        return self._column_lineages.get(lineage_id)

    async def find_all_column_lineages(self) -> List[ColumnLineage]:
        return list(self._column_lineages.values())

    async def find_column_lineages_by_flow(self, flow_id: UUID) -> List[ColumnLineage]:
        return [cl for cl in self._column_lineages.values() if cl.flow_id == flow_id]

    async def find_column_lineages_by_source(self, source_table: str, source_column: str) -> List[ColumnLineage]:
        return [
            cl for cl in self._column_lineages.values()
            if cl.source_table == source_table and cl.source_column == source_column
        ]

    async def save_pipeline(self, pipeline: DataPipeline) -> DataPipeline:
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    async def find_pipeline_by_id(self, pipeline_id: UUID) -> Optional[DataPipeline]:
        return self._pipelines.get(pipeline_id)

    async def find_all_pipelines(self) -> List[DataPipeline]:
        return list(self._pipelines.values())

    async def find_pipelines_by_type(self, pipeline_type: str) -> List[DataPipeline]:
        return [p for p in self._pipelines.values() if p.pipeline_type == pipeline_type]

    async def find_active_pipelines(self) -> List[DataPipeline]:
        return [p for p in self._pipelines.values() if p.is_active]

    async def save_impact_analysis(self, analysis: ImpactAnalysis) -> ImpactAnalysis:
        self._impact_analyses[analysis.analysis_id] = analysis
        return analysis

    async def find_impact_analysis_by_id(self, analysis_id: UUID) -> Optional[ImpactAnalysis]:
        return self._impact_analyses.get(analysis_id)

    async def find_all_impact_analyses(self) -> List[ImpactAnalysis]:
        return list(self._impact_analyses.values())

    async def find_impact_analyses_by_asset(self, asset_id: UUID) -> List[ImpactAnalysis]:
        return [ia for ia in self._impact_analyses.values() if ia.asset_id == asset_id]

    async def save_snapshot(self, snapshot: LineageSnapshot) -> LineageSnapshot:
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    async def find_snapshot_by_id(self, snapshot_id: UUID) -> Optional[LineageSnapshot]:
        return self._snapshots.get(snapshot_id)

    async def find_all_snapshots(self) -> List[LineageSnapshot]:
        return list(self._snapshots.values())

    async def find_latest_snapshot(self) -> Optional[LineageSnapshot]:
        snapshots = list(self._snapshots.values())
        if not snapshots:
            return None
        return max(snapshots, key=lambda s: s.created_at)

    async def save_transformation(self, transformation: DataTransformation) -> DataTransformation:
        self._transformations[transformation.transformation_id] = transformation
        return transformation

    async def find_transformation_by_id(self, transformation_id: UUID) -> Optional[DataTransformation]:
        return self._transformations.get(transformation_id)

    async def find_all_transformations(self) -> List[DataTransformation]:
        return list(self._transformations.values())

    async def find_transformations_by_flow(self, flow_id: UUID) -> List[DataTransformation]:
        return [t for t in self._transformations.values() if t.flow_id == flow_id]

    async def get_statistics(self) -> Dict[str, Any]:
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
