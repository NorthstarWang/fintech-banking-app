"""
Transaction Monitoring Routes

API endpoints for transaction monitoring.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException

from ..models.transaction_pattern_models import (
    PatternType, DetectedPattern, PatternRule, PatternAnalysisRequest, PatternAnalysisResult
)
from ..services.transaction_monitoring_service import transaction_monitoring_service
from ..services.pattern_detection_service import pattern_detection_service

router = APIRouter(prefix="/aml/monitoring", tags=["Transaction Monitoring"])


@router.post("/analyze-transaction")
async def analyze_transaction(transaction: Dict[str, Any], customer_profile: Dict[str, Any]):
    """Analyze a single transaction for suspicious patterns"""
    patterns = await transaction_monitoring_service.monitor_transaction(transaction, customer_profile)
    return {"detected_patterns": patterns}


@router.post("/batch-analysis", response_model=PatternAnalysisResult)
async def run_batch_analysis(request: PatternAnalysisRequest):
    """Run batch pattern analysis"""
    return await transaction_monitoring_service.run_batch_analysis(request)


@router.get("/rules", response_model=List[PatternRule])
async def get_monitoring_rules():
    """Get all monitoring rules"""
    return await transaction_monitoring_service.get_rules()


@router.get("/rules/{rule_id}", response_model=PatternRule)
async def get_monitoring_rule(rule_id: UUID):
    """Get a specific monitoring rule"""
    rule = await transaction_monitoring_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rules", response_model=PatternRule)
async def create_monitoring_rule(rule: PatternRule):
    """Create a new monitoring rule"""
    return await transaction_monitoring_service.create_rule(rule)


@router.put("/rules/{rule_id}")
async def update_monitoring_rule(rule_id: UUID, updates: Dict[str, Any]):
    """Update an existing monitoring rule"""
    rule = await transaction_monitoring_service.update_rule(rule_id, updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: UUID, is_active: bool):
    """Enable or disable a monitoring rule"""
    rule = await transaction_monitoring_service.toggle_rule(rule_id, is_active)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/detect/structuring")
async def detect_structuring(
    customer_id: str, transactions: List[Dict[str, Any]], reporting_threshold: float = 10000.0
):
    """Detect potential structuring patterns"""
    pattern = await pattern_detection_service.detect_structuring(
        customer_id, transactions, reporting_threshold
    )
    return {"pattern": pattern}


@router.post("/detect/layering")
async def detect_layering(transactions: List[Dict[str, Any]], max_hops: int = 10):
    """Detect potential layering patterns"""
    patterns = await pattern_detection_service.detect_layering(transactions, max_hops)
    return {"patterns": patterns}


@router.post("/detect/velocity")
async def detect_velocity_anomaly(
    customer_id: str, current_transactions: List[Dict[str, Any]], historical_stats: Dict[str, Any]
):
    """Detect velocity anomalies"""
    pattern = await pattern_detection_service.detect_velocity_anomaly(
        customer_id, current_transactions, historical_stats
    )
    return {"pattern": pattern}


@router.post("/detect/geographic")
async def detect_geographic_anomaly(
    customer_id: str, transactions: List[Dict[str, Any]],
    expected_countries: List[str], high_risk_countries: List[str]
):
    """Detect geographic anomalies"""
    pattern = await pattern_detection_service.detect_geographic_anomaly(
        customer_id, transactions, expected_countries, high_risk_countries
    )
    return {"pattern": pattern}


@router.post("/detect/rapid-movement")
async def detect_rapid_movement(
    account_id: str, transactions: List[Dict[str, Any]], time_threshold_hours: int = 24
):
    """Detect rapid movement of funds"""
    patterns = await pattern_detection_service.detect_rapid_movement(
        account_id, transactions, time_threshold_hours
    )
    return {"patterns": patterns}


@router.post("/detect/round-tripping")
async def detect_round_tripping(transactions: List[Dict[str, Any]]):
    """Detect round-tripping patterns"""
    patterns = await pattern_detection_service.detect_round_tripping(transactions)
    return {"patterns": patterns}


@router.post("/analyze-flow")
async def analyze_transaction_flow(transactions: List[Dict[str, Any]], root_entity: str):
    """Build and analyze transaction flow"""
    return await pattern_detection_service.analyze_transaction_flow(transactions, root_entity)
