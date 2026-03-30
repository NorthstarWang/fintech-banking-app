"""Credit Score Routes - API endpoints for credit scoring"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.credit_score_models import CreditScore, CreditScoreHistory, ScoreCategory, ScoreType
from ..services.credit_score_service import credit_score_service

router = APIRouter(prefix="/credit/scores", tags=["Credit Scores"])


class CalculateScoreRequest(BaseModel):
    customer_id: str
    score_type: ScoreType = ScoreType.INTERNAL


class RequestScoreRequest(BaseModel):
    customer_id: str
    purpose: str
    requested_by: str


class SimulateScoreRequest(BaseModel):
    customer_id: str
    scenarios: list[dict[str, Any]]
    created_by: str


@router.post("/calculate", response_model=CreditScore)
async def calculate_score(request: CalculateScoreRequest):
    """Calculate credit score for a customer"""
    return await credit_score_service.calculate_score(
        request.customer_id, request.score_type
    )


@router.get("/{score_id}", response_model=CreditScore)
async def get_score(score_id: UUID):
    """Get credit score by ID"""
    score = await credit_score_service.get_score(score_id)
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    return score


@router.get("/customer/{customer_id}", response_model=CreditScore)
async def get_customer_score(customer_id: str):
    """Get latest credit score for a customer"""
    score = await credit_score_service.get_customer_score(customer_id)
    if not score:
        raise HTTPException(status_code=404, detail="No score found for customer")
    return score


@router.get("/customer/{customer_id}/history", response_model=CreditScoreHistory)
async def get_score_history(customer_id: str):
    """Get credit score history for a customer"""
    return await credit_score_service.get_score_history(customer_id)


@router.post("/request")
async def request_score(request: RequestScoreRequest):
    """Request a credit score pull"""
    return await credit_score_service.request_score(
        request.customer_id, request.purpose, request.requested_by
    )


@router.post("/simulate")
async def simulate_score(request: SimulateScoreRequest):
    """Simulate score impact of various scenarios"""
    return await credit_score_service.simulate_score(
        request.customer_id, request.scenarios, request.created_by
    )


@router.get("/")
async def list_scores(
    category: ScoreCategory | None = None,
    min_score: int | None = Query(None, ge=300, le=850),
    max_score: int | None = Query(None, ge=300, le=850),
    limit: int = Query(default=100, le=500)
):
    """List credit scores with optional filters"""
    return {"scores": []}


@router.get("/statistics/summary")
async def get_score_statistics():
    """Get credit score statistics"""
    return await credit_score_service.get_statistics()
