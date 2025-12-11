"""Data Lineage Routes"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.data_lineage_service import data_lineage_service

router = APIRouter(prefix="/data-lineage", tags=["Data Lineage"])


class RegisterAssetRequest(BaseModel):
    asset_name: str
    asset_type: str
    database: str = ""
    schema_name: str = ""
    description: str = ""
    owner: str = ""
    steward: str = ""
    tags: List[str] = []


class CreateFlowRequest(BaseModel):
    flow_name: str
    source_asset_id: UUID
    target_asset_id: UUID
    flow_type: str
    transformation_type: str = ""
    transformation_logic: str = ""
    schedule: str = ""
    created_by: str = ""


class AddColumnLineageRequest(BaseModel):
    flow_id: UUID
    source_column: str
    source_table: str
    target_column: str
    target_table: str
    transformation: str = ""
    discovered_method: str = "manual"


class CreatePipelineRequest(BaseModel):
    pipeline_name: str
    pipeline_type: str
    description: str
    source_systems: List[str]
    target_systems: List[str]
    owner: str


class AddTransformationRequest(BaseModel):
    flow_id: UUID
    transformation_name: str
    transformation_type: str
    source_columns: List[str]
    target_columns: List[str]
    logic: str
    documented_by: str


@router.post("/assets")
async def register_asset(request: RegisterAssetRequest):
    asset = await data_lineage_service.register_asset(
        asset_name=request.asset_name,
        asset_type=request.asset_type,
        database=request.database,
        schema_name=request.schema_name,
        description=request.description,
        owner=request.owner,
        steward=request.steward,
        tags=request.tags,
    )
    return {"status": "registered", "asset_id": str(asset.asset_id)}


@router.get("/assets")
async def get_all_assets():
    assets = await data_lineage_service.repository.find_all_assets()
    return {"assets": [{"asset_id": str(a.asset_id), "name": a.asset_name, "type": a.asset_type} for a in assets]}


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: UUID):
    asset = await data_lineage_service.repository.find_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: UUID):
    deleted = await data_lineage_service.repository.delete_asset(asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"status": "deleted"}


@router.post("/flows")
async def create_flow(request: CreateFlowRequest):
    flow = await data_lineage_service.create_data_flow(
        flow_name=request.flow_name,
        source_asset_id=request.source_asset_id,
        target_asset_id=request.target_asset_id,
        flow_type=request.flow_type,
        transformation_type=request.transformation_type,
        transformation_logic=request.transformation_logic,
        schedule=request.schedule,
        created_by=request.created_by,
    )
    return {"status": "created", "flow_id": str(flow.flow_id)}


@router.get("/flows")
async def get_all_flows():
    flows = await data_lineage_service.repository.find_all_flows()
    return {"flows": [{"flow_id": str(f.flow_id), "name": f.flow_name, "type": f.flow_type} for f in flows]}


@router.get("/flows/{flow_id}")
async def get_flow(flow_id: UUID):
    flow = await data_lineage_service.repository.find_flow_by_id(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


@router.delete("/flows/{flow_id}")
async def delete_flow(flow_id: UUID):
    deleted = await data_lineage_service.repository.delete_flow(flow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flow not found")
    return {"status": "deleted"}


@router.post("/column-lineages")
async def add_column_lineage(request: AddColumnLineageRequest):
    lineage = await data_lineage_service.add_column_lineage(
        flow_id=request.flow_id,
        source_column=request.source_column,
        source_table=request.source_table,
        target_column=request.target_column,
        target_table=request.target_table,
        transformation=request.transformation,
        discovered_method=request.discovered_method,
    )
    return {"status": "created", "lineage_id": str(lineage.lineage_id)}


@router.get("/column-lineages")
async def get_all_column_lineages():
    lineages = await data_lineage_service.repository.find_all_column_lineages()
    return {"lineages": [{"id": str(l.lineage_id), "source": f"{l.source_table}.{l.source_column}"} for l in lineages]}


@router.post("/pipelines")
async def create_pipeline(request: CreatePipelineRequest):
    pipeline = await data_lineage_service.create_pipeline(
        pipeline_name=request.pipeline_name,
        pipeline_type=request.pipeline_type,
        description=request.description,
        source_systems=request.source_systems,
        target_systems=request.target_systems,
        owner=request.owner,
    )
    return {"status": "created", "pipeline_id": str(pipeline.pipeline_id)}


@router.get("/pipelines")
async def get_all_pipelines():
    pipelines = await data_lineage_service.repository.find_all_pipelines()
    return {"pipelines": [{"id": str(p.pipeline_id), "name": p.pipeline_name, "type": p.pipeline_type} for p in pipelines]}


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: UUID):
    pipeline = await data_lineage_service.repository.find_pipeline_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post("/impact-analysis/{asset_id}")
async def perform_impact_analysis(asset_id: UUID, analysis_type: str, performed_by: str):
    analysis = await data_lineage_service.perform_impact_analysis(
        asset_id=asset_id,
        analysis_type=analysis_type,
        performed_by=performed_by,
    )
    return {
        "status": "completed",
        "analysis_id": str(analysis.analysis_id),
        "upstream_count": len(analysis.upstream_assets),
        "downstream_count": len(analysis.downstream_assets),
    }


@router.get("/impact-analysis")
async def get_all_impact_analyses():
    analyses = await data_lineage_service.repository.find_all_impact_analyses()
    return {"analyses": [{"id": str(a.analysis_id), "type": a.analysis_type} for a in analyses]}


@router.post("/snapshots")
async def create_snapshot(snapshot_type: str = "manual"):
    snapshot = await data_lineage_service.create_snapshot(snapshot_type=snapshot_type)
    return {
        "status": "created",
        "snapshot_id": str(snapshot.snapshot_id),
        "assets_captured": snapshot.assets_captured,
        "flows_captured": snapshot.flows_captured,
    }


@router.get("/snapshots")
async def get_all_snapshots():
    snapshots = await data_lineage_service.repository.find_all_snapshots()
    return {"snapshots": [{"id": str(s.snapshot_id), "type": s.snapshot_type, "assets": s.assets_captured} for s in snapshots]}


@router.post("/transformations")
async def add_transformation(request: AddTransformationRequest):
    transformation = await data_lineage_service.add_transformation(
        flow_id=request.flow_id,
        transformation_name=request.transformation_name,
        transformation_type=request.transformation_type,
        source_columns=request.source_columns,
        target_columns=request.target_columns,
        logic=request.logic,
        documented_by=request.documented_by,
    )
    return {"status": "created", "transformation_id": str(transformation.transformation_id)}


@router.get("/transformations")
async def get_all_transformations():
    transformations = await data_lineage_service.repository.find_all_transformations()
    return {"transformations": [{"id": str(t.transformation_id), "name": t.transformation_name} for t in transformations]}


@router.get("/statistics")
async def get_statistics():
    return await data_lineage_service.get_statistics()
