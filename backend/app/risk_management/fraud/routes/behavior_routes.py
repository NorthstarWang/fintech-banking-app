"""Behavior Routes - API endpoints for behavioral analysis"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.behavior_models import (
    BehaviorPattern, BehaviorEvent, BehaviorAnomaly,
    BehaviorScore, BehaviorCategory, AnomalyType
)
from ..services.behavior_service import behavior_service


router = APIRouter(prefix="/fraud/behavior", tags=["Fraud Behavior"])


class CreatePatternRequest(BaseModel):
    customer_id: str


class RecordEventRequest(BaseModel):
    customer_id: str
    event_type: str
    category: BehaviorCategory
    event_data: Dict[str, Any]


class RecordAnomalyRequest(BaseModel):
    customer_id: str
    event_id: UUID
    anomaly_type: AnomalyType
    description: str


class ResolveAnomalyRequest(BaseModel):
    resolution: str
    resolved_by: str


class UpdatePatternRequest(BaseModel):
    typical_login_times: Optional[List[int]] = None
    typical_devices: Optional[List[str]] = None
    typical_locations: Optional[List[str]] = None
    average_transaction_amount: Optional[float] = None
    typical_transaction_count_daily: Optional[int] = None


@router.post("/patterns", response_model=BehaviorPattern)
async def create_pattern(request: CreatePatternRequest):
    """Create a behavior pattern for a customer"""
    pattern = await behavior_service.create_pattern(request.customer_id)
    return pattern


@router.get("/patterns/{customer_id}", response_model=BehaviorPattern)
async def get_pattern(customer_id: str):
    """Get behavior pattern for a customer"""
    pattern = await behavior_service.get_pattern(customer_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern


@router.put("/patterns/{customer_id}")
async def update_pattern(customer_id: str, request: UpdatePatternRequest):
    """Update a behavior pattern"""
    pattern = await behavior_service.get_pattern(customer_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    updates = request.model_dump(exclude_none=True)
    for key, value in updates.items():
        if hasattr(pattern, key):
            setattr(pattern, key, value)
    return pattern


@router.post("/events", response_model=BehaviorEvent)
async def record_event(request: RecordEventRequest):
    """Record a behavior event"""
    event = await behavior_service.record_event(
        customer_id=request.customer_id,
        event_type=request.event_type,
        category=request.category,
        event_data=request.event_data
    )
    return event


@router.get("/events/{customer_id}")
async def get_customer_events(
    customer_id: str,
    category: Optional[BehaviorCategory] = None,
    limit: int = Query(default=100, le=500)
):
    """Get behavior events for a customer"""
    # This would typically query the repository
    return {"customer_id": customer_id, "events": []}


@router.post("/anomalies", response_model=BehaviorAnomaly)
async def record_anomaly(request: RecordAnomalyRequest):
    """Record a behavior anomaly"""
    anomaly = await behavior_service.record_anomaly(
        customer_id=request.customer_id,
        event_id=request.event_id,
        anomaly_type=request.anomaly_type,
        description=request.description
    )
    return anomaly


@router.get("/anomalies/{customer_id}")
async def get_customer_anomalies(
    customer_id: str,
    anomaly_type: Optional[AnomalyType] = None,
    unresolved_only: bool = False,
    limit: int = Query(default=100, le=500)
):
    """Get anomalies for a customer"""
    return {"customer_id": customer_id, "anomalies": []}


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(anomaly_id: UUID, request: ResolveAnomalyRequest):
    """Resolve a behavior anomaly"""
    # This would call the service method
    return {
        "anomaly_id": str(anomaly_id),
        "resolved": True,
        "resolution": request.resolution,
        "resolved_by": request.resolved_by
    }


@router.get("/scores/{customer_id}", response_model=BehaviorScore)
async def get_behavior_score(customer_id: str):
    """Get or calculate behavior score for a customer"""
    score = await behavior_service.calculate_behavior_score(customer_id)
    return score


@router.post("/scores/{customer_id}/refresh", response_model=BehaviorScore)
async def refresh_behavior_score(customer_id: str):
    """Recalculate behavior score for a customer"""
    score = await behavior_service.calculate_behavior_score(customer_id)
    return score


@router.get("/high-risk")
async def get_high_risk_customers(
    threshold: float = Query(default=50.0, ge=0, le=100),
    limit: int = Query(default=100, le=500)
):
    """Get customers with low behavior scores (high risk)"""
    return {"high_risk_customers": []}


@router.post("/analyze")
async def analyze_behavior(
    customer_id: str,
    event_type: str,
    event_data: Dict[str, Any]
):
    """Analyze a behavior event for anomalies"""
    # Create pattern if it doesn't exist
    pattern = await behavior_service.get_pattern(customer_id)
    if not pattern:
        pattern = await behavior_service.create_pattern(customer_id)

    # Record and analyze the event
    event = await behavior_service.record_event(
        customer_id=customer_id,
        event_type=event_type,
        category=BehaviorCategory.TRANSACTION,
        event_data=event_data
    )

    # Calculate score
    score = await behavior_service.calculate_behavior_score(customer_id)

    return {
        "event": event,
        "is_anomalous": event.is_anomalous,
        "anomaly_score": event.anomaly_score,
        "behavior_score": score
    }


@router.get("/statistics/summary")
async def get_behavior_statistics():
    """Get behavior analysis statistics"""
    return await behavior_service.get_statistics()
