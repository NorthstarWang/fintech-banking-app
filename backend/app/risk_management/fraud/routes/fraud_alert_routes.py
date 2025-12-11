"""Fraud Alert Routes - API endpoints for fraud alert management"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.fraud_alert_models import (
    FraudAlert, FraudAlertStatus, FraudAlertSeverity, FraudType
)
from ..services.fraud_alert_service import fraud_alert_service


router = APIRouter(prefix="/fraud/alerts", tags=["Fraud Alerts"])


class CreateAlertRequest(BaseModel):
    fraud_type: FraudType
    severity: FraudAlertSeverity
    customer_id: str
    customer_name: str
    transaction_id: Optional[str] = None
    transaction_amount: Optional[float] = None
    fraud_score: float = Field(ge=0, le=100)
    description: str
    detection_method: str
    risk_indicators: List[str] = []


class UpdateAlertRequest(BaseModel):
    status: Optional[FraudAlertStatus] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    resolution: Optional[str] = None


class AssignAlertRequest(BaseModel):
    assigned_to: str


class EscalateAlertRequest(BaseModel):
    escalated_to: str
    reason: str


class BulkAssignRequest(BaseModel):
    alert_ids: List[UUID]
    assigned_to: str


@router.post("/", response_model=FraudAlert)
async def create_alert(request: CreateAlertRequest):
    """Create a new fraud alert"""
    alert = await fraud_alert_service.create_alert(
        fraud_type=request.fraud_type,
        severity=request.severity,
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        transaction_id=request.transaction_id,
        transaction_amount=request.transaction_amount,
        fraud_score=request.fraud_score,
        description=request.description,
        detection_method=request.detection_method,
        risk_indicators=request.risk_indicators
    )
    return alert


@router.get("/{alert_id}", response_model=FraudAlert)
async def get_alert(alert_id: UUID):
    """Get fraud alert by ID"""
    alert = await fraud_alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/{alert_id}", response_model=FraudAlert)
async def update_alert(alert_id: UUID, request: UpdateAlertRequest):
    """Update a fraud alert"""
    updates = request.model_dump(exclude_none=True)
    alert = await fraud_alert_service.update_alert(alert_id, updates)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/assign", response_model=FraudAlert)
async def assign_alert(alert_id: UUID, request: AssignAlertRequest):
    """Assign an alert to an analyst"""
    alert = await fraud_alert_service.assign_alert(alert_id, request.assigned_to)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/escalate", response_model=FraudAlert)
async def escalate_alert(alert_id: UUID, request: EscalateAlertRequest):
    """Escalate an alert"""
    alert = await fraud_alert_service.escalate_alert(
        alert_id, request.escalated_to, request.reason
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/close", response_model=FraudAlert)
async def close_alert(alert_id: UUID, resolution: str, closed_by: str):
    """Close an alert"""
    alert = await fraud_alert_service.close_alert(alert_id, resolution, closed_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/dismiss", response_model=FraudAlert)
async def dismiss_alert(alert_id: UUID, reason: str, dismissed_by: str):
    """Dismiss an alert as false positive"""
    alert = await fraud_alert_service.dismiss_alert(alert_id, reason, dismissed_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/", response_model=List[FraudAlert])
async def list_alerts(
    status: Optional[FraudAlertStatus] = None,
    severity: Optional[FraudAlertSeverity] = None,
    fraud_type: Optional[FraudType] = None,
    customer_id: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List fraud alerts with optional filters"""
    alerts = await fraud_alert_service.get_alerts_by_status(
        status or FraudAlertStatus.NEW
    )
    return alerts[:limit]


@router.get("/high-priority", response_model=List[FraudAlert])
async def get_high_priority_alerts(limit: int = Query(default=50, le=200)):
    """Get high priority alerts requiring attention"""
    return await fraud_alert_service.get_high_priority_alerts(limit)


@router.get("/customer/{customer_id}", response_model=List[FraudAlert])
async def get_customer_alerts(customer_id: str, limit: int = Query(default=50, le=200)):
    """Get all alerts for a specific customer"""
    return await fraud_alert_service.get_alerts_by_customer(customer_id)


@router.post("/bulk-assign")
async def bulk_assign_alerts(request: BulkAssignRequest):
    """Assign multiple alerts to an analyst"""
    results = []
    for alert_id in request.alert_ids:
        alert = await fraud_alert_service.assign_alert(alert_id, request.assigned_to)
        results.append({"alert_id": alert_id, "success": alert is not None})
    return {"results": results}


@router.get("/statistics/summary")
async def get_alert_statistics():
    """Get alert statistics"""
    return await fraud_alert_service.get_statistics()
