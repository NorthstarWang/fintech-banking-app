"""
Sanctions Screening Routes

API endpoints for sanctions screening.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.sanction_models import (
    SanctionListType, ScreeningRequest, ScreeningResult, SanctionListEntry,
    BatchScreeningJob, SanctionListUpdate
)
from ..services.sanctions_screening_service import sanctions_screening_service

router = APIRouter(prefix="/aml/sanctions", tags=["Sanctions Screening"])


@router.post("/screen", response_model=ScreeningResult)
async def screen_entity(request: ScreeningRequest):
    """Screen an entity against sanctions lists"""
    return await sanctions_screening_service.screen_entity(request)


@router.post("/batch-screen")
async def batch_screen(entities: List[Dict[str, Any]], job_name: str, created_by: str = "system"):
    """Start a batch screening job"""
    return await sanctions_screening_service.batch_screen(entities, job_name, created_by)


@router.get("/results/{result_id}", response_model=ScreeningResult)
async def get_screening_result(result_id: UUID):
    """Get screening result by ID"""
    result = await sanctions_screening_service.get_screening_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/jobs/{job_id}")
async def get_batch_job(job_id: UUID):
    """Get batch job by ID"""
    job = await sanctions_screening_service.get_batch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/lists/{list_type}/entries", response_model=List[SanctionListEntry])
async def get_sanction_entries(list_type: Optional[SanctionListType] = None):
    """Get sanctions list entries"""
    return await sanctions_screening_service.get_sanction_entries(list_type)


@router.post("/lists/entries")
async def add_sanction_entry(entry: SanctionListEntry):
    """Add a new sanctions list entry"""
    return await sanctions_screening_service.add_sanction_entry(entry)


@router.put("/lists/entries/{entry_id}")
async def update_sanction_entry(entry_id: UUID, updates: Dict[str, Any]):
    """Update a sanctions list entry"""
    entry = await sanctions_screening_service.update_sanction_entry(entry_id, updates)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/lists/import")
async def import_list_update(update: SanctionListUpdate):
    """Import updates to a sanctions list"""
    return await sanctions_screening_service.import_list_update(update)


@router.get("/statistics")
async def get_statistics():
    """Get sanctions screening statistics"""
    return await sanctions_screening_service.get_statistics()
