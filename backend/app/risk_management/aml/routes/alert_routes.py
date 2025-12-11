"""
AML Alert Routes

API endpoints for AML alert management.
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models.alert_models import (
    AMLAlert, AlertSummary, AlertStatistics, AlertStatus, AlertSeverity,
    AlertType, AlertCreateRequest, AlertUpdateRequest, AlertSearchCriteria
)
from ..services.alert_service import alert_service

router = APIRouter(prefix="/aml/alerts", tags=["AML Alerts"])


@router.post("/", response_model=AMLAlert)
async def create_alert(request: AlertCreateRequest, created_by: str = "system"):
    """Create a new AML alert"""
    return await alert_service.create_alert(request, created_by)


@router.get("/{alert_id}", response_model=AMLAlert)
async def get_alert(alert_id: UUID):
    """Get alert by ID"""
    alert = await alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/{alert_id}", response_model=AMLAlert)
async def update_alert(alert_id: UUID, request: AlertUpdateRequest, updated_by: str = "system"):
    """Update an alert"""
    alert = await alert_service.update_alert(alert_id, request, updated_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/assign")
async def assign_alert(alert_id: UUID, assignee: str, assigned_by: str = "system"):
    """Assign alert to an analyst"""
    alert = await alert_service.assign_alert(alert_id, assignee, assigned_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/comment")
async def add_comment(
    alert_id: UUID, content: str, author_id: str, author_name: str, is_internal: bool = True
):
    """Add comment to an alert"""
    alert = await alert_service.add_comment(alert_id, author_id, author_name, content, is_internal)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success"}


@router.post("/{alert_id}/escalate")
async def escalate_alert(alert_id: UUID, reason: str, escalated_by: str = "system"):
    """Escalate an alert"""
    alert = await alert_service.escalate_alert(alert_id, escalated_by, reason)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/close")
async def close_alert(
    alert_id: UUID, is_true_positive: bool, notes: str, closed_by: str = "system"
):
    """Close an alert"""
    alert = await alert_service.close_alert(alert_id, closed_by, is_true_positive, notes)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/search", response_model=List[AlertSummary])
async def search_alerts(criteria: AlertSearchCriteria):
    """Search alerts based on criteria"""
    return await alert_service.search_alerts(criteria)


@router.get("/statistics", response_model=AlertStatistics)
async def get_statistics():
    """Get alert statistics"""
    return await alert_service.get_statistics()


@router.get("/customer/{customer_id}", response_model=List[AMLAlert])
async def get_alerts_for_customer(customer_id: str):
    """Get all alerts for a customer"""
    return await alert_service.get_alerts_for_customer(customer_id)


@router.get("/open", response_model=List[AMLAlert])
async def get_open_alerts():
    """Get all open alerts"""
    return await alert_service.get_open_alerts()
