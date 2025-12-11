"""Fraud Pattern Routes - API endpoints for fraud pattern management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.fraud_pattern_models import (
    FraudPattern, PatternMatch, PatternCategory, PatternStatus, RiskLevel
)


router = APIRouter(prefix="/fraud/patterns", tags=["Fraud Patterns"])


class PatternIndicatorRequest(BaseModel):
    indicator_name: str
    indicator_type: str
    threshold: Optional[float] = None
    weight: float = Field(default=1.0, ge=0, le=10)


class CreatePatternRequest(BaseModel):
    pattern_code: str
    pattern_name: str
    category: PatternCategory
    description: str
    indicators: List[PatternIndicatorRequest]
    risk_level: RiskLevel = RiskLevel.MEDIUM
    min_confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    created_by: str


class UpdatePatternRequest(BaseModel):
    pattern_name: Optional[str] = None
    description: Optional[str] = None
    indicators: Optional[List[PatternIndicatorRequest]] = None
    risk_level: Optional[RiskLevel] = None
    min_confidence_threshold: Optional[float] = None
    status: Optional[PatternStatus] = None


class RecordMatchRequest(BaseModel):
    pattern_id: UUID
    entity_type: str
    entity_id: str
    matched_indicators: List[str]
    confidence_score: float = Field(ge=0, le=1)
    matched_data: Dict[str, Any] = {}


class ReviewMatchRequest(BaseModel):
    reviewed_by: str
    is_valid: bool
    review_notes: Optional[str] = None


# In-memory storage for demo
_patterns: Dict[UUID, FraudPattern] = {}
_matches: List[PatternMatch] = []


@router.post("/", response_model=FraudPattern)
async def create_pattern(request: CreatePatternRequest):
    """Create a new fraud pattern"""
    from ..models.fraud_pattern_models import PatternIndicator

    indicators = [
        PatternIndicator(
            indicator_name=i.indicator_name,
            indicator_type=i.indicator_type,
            threshold=i.threshold,
            weight=i.weight
        )
        for i in request.indicators
    ]

    pattern = FraudPattern(
        pattern_code=request.pattern_code,
        pattern_name=request.pattern_name,
        category=request.category,
        description=request.description,
        indicators=indicators,
        risk_level=request.risk_level,
        min_confidence_threshold=request.min_confidence_threshold,
        created_by=request.created_by
    )
    _patterns[pattern.pattern_id] = pattern
    return pattern


@router.get("/{pattern_id}", response_model=FraudPattern)
async def get_pattern(pattern_id: UUID):
    """Get pattern by ID"""
    pattern = _patterns.get(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern


@router.put("/{pattern_id}", response_model=FraudPattern)
async def update_pattern(pattern_id: UUID, request: UpdatePatternRequest):
    """Update a fraud pattern"""
    pattern = _patterns.get(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    updates = request.model_dump(exclude_none=True)
    for key, value in updates.items():
        if hasattr(pattern, key):
            setattr(pattern, key, value)
    return pattern


@router.delete("/{pattern_id}")
async def delete_pattern(pattern_id: UUID):
    """Delete a fraud pattern"""
    if pattern_id not in _patterns:
        raise HTTPException(status_code=404, detail="Pattern not found")
    del _patterns[pattern_id]
    return {"message": "Pattern deleted successfully", "pattern_id": str(pattern_id)}


@router.post("/{pattern_id}/activate", response_model=FraudPattern)
async def activate_pattern(pattern_id: UUID):
    """Activate a pattern"""
    pattern = _patterns.get(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    pattern.status = PatternStatus.ACTIVE
    return pattern


@router.post("/{pattern_id}/deactivate", response_model=FraudPattern)
async def deactivate_pattern(pattern_id: UUID):
    """Deactivate a pattern"""
    pattern = _patterns.get(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    pattern.status = PatternStatus.INACTIVE
    return pattern


@router.get("/", response_model=List[FraudPattern])
async def list_patterns(
    category: Optional[PatternCategory] = None,
    status: Optional[PatternStatus] = None,
    risk_level: Optional[RiskLevel] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List fraud patterns with optional filters"""
    patterns = list(_patterns.values())
    if category:
        patterns = [p for p in patterns if p.category == category]
    if status:
        patterns = [p for p in patterns if p.status == status]
    if risk_level:
        patterns = [p for p in patterns if p.risk_level == risk_level]
    return patterns[offset:offset + limit]


@router.get("/active", response_model=List[FraudPattern])
async def get_active_patterns():
    """Get all active patterns"""
    return [p for p in _patterns.values() if p.status == PatternStatus.ACTIVE]


@router.get("/high-risk", response_model=List[FraudPattern])
async def get_high_risk_patterns():
    """Get high-risk patterns"""
    return [
        p for p in _patterns.values()
        if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    ]


@router.post("/matches", response_model=PatternMatch)
async def record_match(request: RecordMatchRequest):
    """Record a pattern match"""
    pattern = _patterns.get(request.pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    match = PatternMatch(
        pattern_id=request.pattern_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        matched_indicators=request.matched_indicators,
        confidence_score=request.confidence_score,
        matched_data=request.matched_data
    )
    _matches.append(match)
    pattern.match_count += 1
    return match


@router.get("/matches/{match_id}", response_model=PatternMatch)
async def get_match(match_id: UUID):
    """Get match by ID"""
    for match in _matches:
        if match.match_id == match_id:
            return match
    raise HTTPException(status_code=404, detail="Match not found")


@router.post("/matches/{match_id}/review")
async def review_match(match_id: UUID, request: ReviewMatchRequest):
    """Review a pattern match"""
    for match in _matches:
        if match.match_id == match_id:
            match.reviewed = True
            match.reviewed_by = request.reviewed_by
            match.review_result = "valid" if request.is_valid else "invalid"
            return {"message": "Match reviewed successfully", "match_id": str(match_id)}
    raise HTTPException(status_code=404, detail="Match not found")


@router.get("/matches")
async def list_matches(
    pattern_id: Optional[UUID] = None,
    entity_type: Optional[str] = None,
    reviewed: Optional[bool] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List pattern matches with optional filters"""
    matches = _matches
    if pattern_id:
        matches = [m for m in matches if m.pattern_id == pattern_id]
    if entity_type:
        matches = [m for m in matches if m.entity_type == entity_type]
    if reviewed is not None:
        matches = [m for m in matches if m.reviewed == reviewed]
    return matches[offset:offset + limit]


@router.get("/{pattern_id}/matches")
async def get_pattern_matches(
    pattern_id: UUID,
    limit: int = Query(default=100, le=500)
):
    """Get matches for a specific pattern"""
    pattern = _patterns.get(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    matches = [m for m in _matches if m.pattern_id == pattern_id]
    return matches[:limit]


@router.get("/statistics/summary")
async def get_pattern_statistics():
    """Get pattern statistics"""
    total_patterns = len(_patterns)
    active_patterns = len([p for p in _patterns.values() if p.status == PatternStatus.ACTIVE])
    by_category = {}
    for pattern in _patterns.values():
        cat_key = pattern.category.value
        by_category[cat_key] = by_category.get(cat_key, 0) + 1
    by_risk_level = {}
    for pattern in _patterns.values():
        risk_key = pattern.risk_level.value
        by_risk_level[risk_key] = by_risk_level.get(risk_key, 0) + 1
    return {
        "total_patterns": total_patterns,
        "active_patterns": active_patterns,
        "by_category": by_category,
        "by_risk_level": by_risk_level,
        "total_matches": len(_matches)
    }
