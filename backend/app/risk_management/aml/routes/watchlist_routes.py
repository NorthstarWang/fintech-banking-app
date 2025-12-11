"""
Watchlist Routes

API endpoints for watchlist management.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.watchlist_models import (
    Watchlist, WatchlistEntry, WatchlistType, WatchlistCategory,
    WatchlistScreeningRequest, WatchlistScreeningResult, WatchlistStatistics
)
from ..services.watchlist_service import watchlist_service

router = APIRouter(prefix="/aml/watchlists", tags=["Watchlists"])


@router.post("/", response_model=Watchlist)
async def create_watchlist(
    name: str, code: str, watchlist_type: WatchlistType, description: str,
    default_category: WatchlistCategory, owner_team: str, created_by: str = "system"
):
    """Create a new watchlist"""
    return await watchlist_service.create_watchlist(
        name, code, watchlist_type, description, default_category, owner_team, created_by
    )


@router.get("/", response_model=List[Watchlist])
async def get_all_watchlists():
    """Get all watchlists"""
    return await watchlist_service.get_all_watchlists()


@router.get("/{watchlist_id}", response_model=Watchlist)
async def get_watchlist(watchlist_id: UUID):
    """Get watchlist by ID"""
    watchlist = await watchlist_service.get_watchlist(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@router.put("/{watchlist_id}")
async def update_watchlist(watchlist_id: UUID, updates: Dict[str, Any], updated_by: str = "system"):
    """Update a watchlist"""
    watchlist = await watchlist_service.update_watchlist(watchlist_id, updates, updated_by)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@router.post("/{watchlist_id}/entries")
async def add_entry(watchlist_id: UUID, entry_data: Dict[str, Any], created_by: str = "system"):
    """Add entry to a watchlist"""
    try:
        return await watchlist_service.add_entry(watchlist_id, entry_data, created_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/entries/{entry_id}")
async def get_entry(entry_id: UUID):
    """Get watchlist entry by ID"""
    entry = await watchlist_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.put("/entries/{entry_id}")
async def update_entry(entry_id: UUID, updates: Dict[str, Any], updated_by: str = "system"):
    """Update a watchlist entry"""
    entry = await watchlist_service.update_entry(entry_id, updates, updated_by)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/entries/{entry_id}/deactivate")
async def deactivate_entry(entry_id: UUID, reason: str, deactivated_by: str = "system"):
    """Deactivate a watchlist entry"""
    entry = await watchlist_service.deactivate_entry(entry_id, reason, deactivated_by)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.get("/entries/search")
async def search_entries(
    query: str, watchlist_ids: Optional[List[UUID]] = None,
    categories: Optional[List[WatchlistCategory]] = None, active_only: bool = True
):
    """Search watchlist entries"""
    return await watchlist_service.search_entries(query, watchlist_ids, categories, active_only)


@router.post("/screen", response_model=WatchlistScreeningResult)
async def screen_entity(request: WatchlistScreeningRequest):
    """Screen an entity against watchlists"""
    return await watchlist_service.screen_entity(request)


@router.post("/matches/{match_id}/review")
async def review_match(
    match_id: UUID, status: str, reviewed_by: str, notes: Optional[str] = None
):
    """Review a watchlist match"""
    match = await watchlist_service.review_match(match_id, status, reviewed_by, notes)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.get("/statistics", response_model=WatchlistStatistics)
async def get_statistics():
    """Get watchlist statistics"""
    return await watchlist_service.get_statistics()
