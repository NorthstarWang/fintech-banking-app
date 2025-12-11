"""Data Lineage Service"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.data_lineage_models import (
    DataAsset, DataFlow, ColumnLineage, DataPipeline,
    ImpactAnalysis, LineageSnapshot, DataTransformation
)
from ..repositories.data_lineage_repository import data_lineage_repository


class DataLineageService:
    def __init__(self):
        self.repository = data_lineage_repository

    async def register_asset(
        self, asset_name: str, asset_type: str, database: str = "",
        schema_name: str = "", description: str = "", owner: str = "",
        steward: str = "", tags: List[str] = None
    ) -> DataAsset:
        asset = DataAsset(
            asset_name=asset_name, asset_type=asset_type, database=database,
            schema_name=schema_name, description=description, owner=owner,
            steward=steward, tags=tags or []
        )
        await self.repository.save_asset(asset)
        return asset

    async def create_data_flow(
        self, flow_name: str, source_asset_id: UUID, target_asset_id: UUID,
        flow_type: str, transformation_type: str = "", transformation_logic: str = "",
        schedule: str = "", created_by: str = ""
    ) -> DataFlow:
        flow = DataFlow(
            flow_name=flow_name, source_asset_id=source_asset_id,
            target_asset_id=target_asset_id, flow_type=flow_type,
            transformation_type=transformation_type, transformation_logic=transformation_logic,
            schedule=schedule, created_by=created_by
        )
        await self.repository.save_flow(flow)
        return flow

    async def add_column_lineage(
        self, flow_id: UUID, source_column: str, source_table: str,
        target_column: str, target_table: str, transformation: str = "",
        discovered_method: str = "manual"
    ) -> ColumnLineage:
        lineage = ColumnLineage(
            flow_id=flow_id, source_column=source_column, source_table=source_table,
            target_column=target_column, target_table=target_table,
            transformation=transformation, discovered_method=discovered_method
        )
        await self.repository.save_column_lineage(lineage)
        return lineage

    async def create_pipeline(
        self, pipeline_name: str, pipeline_type: str, description: str,
        source_systems: List[str], target_systems: List[str], owner: str
    ) -> DataPipeline:
        pipeline = DataPipeline(
            pipeline_name=pipeline_name, pipeline_type=pipeline_type,
            description=description, source_systems=source_systems,
            target_systems=target_systems, owner=owner
        )
        await self.repository.save_pipeline(pipeline)
        return pipeline

    async def perform_impact_analysis(
        self, asset_id: UUID, analysis_type: str, performed_by: str
    ) -> ImpactAnalysis:
        upstream = []
        downstream = []

        flows = await self.repository.find_all_flows()

        for flow in flows:
            if flow.target_asset_id == asset_id:
                source = await self.repository.find_asset_by_id(flow.source_asset_id)
                if source:
                    upstream.append({"asset_id": str(source.asset_id), "asset_name": source.asset_name})
            if flow.source_asset_id == asset_id:
                target = await self.repository.find_asset_by_id(flow.target_asset_id)
                if target:
                    downstream.append({"asset_id": str(target.asset_id), "asset_name": target.asset_name})

        analysis = ImpactAnalysis(
            asset_id=asset_id, analysis_type=analysis_type,
            upstream_assets=upstream, downstream_assets=downstream,
            performed_by=performed_by
        )
        await self.repository.save_impact_analysis(analysis)
        return analysis

    async def create_snapshot(self, snapshot_type: str = "scheduled") -> LineageSnapshot:
        assets = await self.repository.find_all_assets()
        flows = await self.repository.find_all_flows()
        lineages = await self.repository.find_all_column_lineages()

        snapshot = LineageSnapshot(
            snapshot_type=snapshot_type, assets_captured=len(assets),
            flows_captured=len(flows), lineages_captured=len(lineages)
        )
        await self.repository.save_snapshot(snapshot)
        return snapshot

    async def add_transformation(
        self, flow_id: UUID, transformation_name: str, transformation_type: str,
        source_columns: List[str], target_columns: List[str], logic: str,
        documented_by: str
    ) -> DataTransformation:
        transformation = DataTransformation(
            flow_id=flow_id, transformation_name=transformation_name,
            transformation_type=transformation_type, source_columns=source_columns,
            target_columns=target_columns, logic=logic, documented_by=documented_by
        )
        await self.repository.save_transformation(transformation)
        return transformation

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


data_lineage_service = DataLineageService()
