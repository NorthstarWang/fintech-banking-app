"""Rating Routes - API endpoints for credit rating management"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.rating_models import (
    CreditRating, RatingMigration, RatingReview, RatingOverride,
    RatingType, RatingOutlook
)
from ..services.rating_service import rating_service

router = APIRouter(prefix="/credit/ratings", tags=["Credit Ratings"])


class AssignRatingRequest(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    rating_grade: str
    rating_rationale: str
    rated_by: str


class UpdateOutlookRequest(BaseModel):
    outlook: RatingOutlook


class CreateReviewRequest(BaseModel):
    review_type: str
    proposed_rating: str
    rating_action: str
    recommendation: str
    reviewed_by: str


class ApplyOverrideRequest(BaseModel):
    override_rating: str
    override_reason: str
    override_type: str
    approved_by: str


@router.post("/", response_model=CreditRating)
async def assign_rating(request: AssignRatingRequest):
    """Assign a credit rating"""
    rating = await rating_service.assign_rating(
        request.entity_id, request.entity_name, request.entity_type,
        request.rating_grade, request.rating_rationale, request.rated_by
    )
    return rating


@router.get("/{rating_id}", response_model=CreditRating)
async def get_rating(rating_id: UUID):
    """Get rating by ID"""
    rating = await rating_service.get_rating(rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@router.get("/entity/{entity_id}", response_model=CreditRating)
async def get_entity_rating(entity_id: str):
    """Get rating for an entity"""
    rating = await rating_service.get_entity_rating(entity_id)
    if not rating:
        raise HTTPException(status_code=404, detail="No rating found for entity")
    return rating


@router.put("/{rating_id}/outlook", response_model=CreditRating)
async def update_outlook(rating_id: UUID, request: UpdateOutlookRequest):
    """Update rating outlook"""
    rating = await rating_service.update_outlook(rating_id, request.outlook)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@router.post("/{rating_id}/reviews", response_model=RatingReview)
async def create_review(rating_id: UUID, request: CreateReviewRequest):
    """Create a rating review"""
    review = await rating_service.create_review(
        rating_id, request.review_type, request.proposed_rating,
        request.rating_action, request.recommendation, request.reviewed_by
    )
    if not review:
        raise HTTPException(status_code=404, detail="Rating not found")
    return review


@router.post("/{rating_id}/overrides", response_model=RatingOverride)
async def apply_override(rating_id: UUID, request: ApplyOverrideRequest):
    """Apply a rating override"""
    override = await rating_service.apply_override(
        rating_id, request.override_rating, request.override_reason,
        request.override_type, request.approved_by
    )
    if not override:
        raise HTTPException(status_code=404, detail="Rating not found")
    return override


@router.get("/grade/{grade}", response_model=List[CreditRating])
async def get_ratings_by_grade(grade: str):
    """Get all ratings with a specific grade"""
    return await rating_service.get_ratings_by_grade(grade)


@router.get("/migrations")
async def get_migrations(entity_id: Optional[str] = None):
    """Get rating migrations"""
    return await rating_service.get_migrations(entity_id)


@router.get("/")
async def list_ratings(
    rating_type: Optional[RatingType] = None,
    outlook: Optional[RatingOutlook] = None,
    grade: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """List ratings with optional filters"""
    return {"ratings": []}


@router.get("/statistics/summary")
async def get_rating_statistics():
    """Get rating statistics"""
    return await rating_service.get_statistics()
