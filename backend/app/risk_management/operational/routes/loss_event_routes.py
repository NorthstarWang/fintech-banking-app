"""Loss Event Routes - API endpoints for operational loss tracking"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.loss_event_models import (
    LossEvent, LossRecovery, LossProvision, LossEventCausality,
    LossDistribution, OperationalLossCapital, LossEventReport,
    LossEventType, LossEventStatus, RecoveryType
)
from ..services.loss_event_service import loss_event_service

router = APIRouter(prefix="/loss-events", tags=["Loss Events"])


class CreateLossEventRequest(BaseModel):
    event_type: LossEventType
    event_description: str
    discovery_date: date
    occurrence_date: date
    accounting_date: date
    business_line: str
    business_unit: str
    legal_entity: str
    country: str
    gross_loss: Decimal
    reported_by: str
    near_miss: bool = False
    near_miss_amount: Optional[Decimal] = None
    related_incident_id: Optional[UUID] = None


class UpdateStatusRequest(BaseModel):
    new_status: LossEventStatus
    updated_by: str


class RecoveryRequest(BaseModel):
    recovery_type: RecoveryType
    recovery_amount: Decimal
    recovery_date: date
    source: str
    reference_number: Optional[str] = None


class ProvisionRequest(BaseModel):
    provision_type: str
    provision_amount: Decimal
    provision_date: date
    approved_by: str


class CausalityRequest(BaseModel):
    cause_category: str
    cause_subcategory: str
    cause_description: str
    contributing_factor: bool = False
    control_failure: bool = False
    failed_control_id: Optional[UUID] = None


class CapitalRequest(BaseModel):
    methodology: str
    business_indicator: Decimal
    confidence_level: Decimal = Decimal("0.999")
    time_horizon: int = 1


@router.post("/", response_model=LossEvent)
async def create_loss_event(request: CreateLossEventRequest):
    """Create new loss event"""
    return await loss_event_service.create_loss_event(
        event_type=request.event_type,
        event_description=request.event_description,
        discovery_date=request.discovery_date,
        occurrence_date=request.occurrence_date,
        accounting_date=request.accounting_date,
        business_line=request.business_line,
        business_unit=request.business_unit,
        legal_entity=request.legal_entity,
        country=request.country,
        gross_loss=request.gross_loss,
        reported_by=request.reported_by,
        near_miss=request.near_miss,
        near_miss_amount=request.near_miss_amount,
        related_incident_id=request.related_incident_id
    )


@router.get("/{event_id}", response_model=LossEvent)
async def get_event(event_id: UUID):
    """Get loss event by ID"""
    event = await loss_event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Loss event not found")
    return event


@router.get("/reference/{reference}", response_model=LossEvent)
async def get_event_by_reference(reference: str):
    """Get loss event by reference"""
    event = await loss_event_service.get_event_by_reference(reference)
    if not event:
        raise HTTPException(status_code=404, detail="Loss event not found")
    return event


@router.get("/", response_model=List[LossEvent])
async def list_events(
    event_type: Optional[LossEventType] = Query(None),
    status: Optional[LossEventStatus] = Query(None),
    business_line: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_loss: Optional[Decimal] = Query(None)
):
    """List loss events with filters"""
    return await loss_event_service.list_events(
        event_type, status, business_line, start_date, end_date, min_loss
    )


@router.put("/{event_id}/status", response_model=LossEvent)
async def update_status(event_id: UUID, request: UpdateStatusRequest):
    """Update loss event status"""
    event = await loss_event_service.update_event_status(
        event_id, request.new_status, request.updated_by
    )
    if not event:
        raise HTTPException(status_code=404, detail="Loss event not found")
    return event


@router.post("/{event_id}/recoveries", response_model=LossRecovery)
async def add_recovery(event_id: UUID, request: RecoveryRequest):
    """Add recovery to loss event"""
    return await loss_event_service.add_recovery(
        event_id=event_id,
        recovery_type=request.recovery_type,
        recovery_amount=request.recovery_amount,
        recovery_date=request.recovery_date,
        source=request.source,
        reference_number=request.reference_number
    )


@router.get("/{event_id}/recoveries", response_model=List[LossRecovery])
async def get_recoveries(event_id: UUID):
    """Get recoveries for loss event"""
    return await loss_event_service.get_event_recoveries(event_id)


@router.post("/{event_id}/provisions", response_model=LossProvision)
async def add_provision(event_id: UUID, request: ProvisionRequest):
    """Add provision for loss event"""
    return await loss_event_service.add_provision(
        event_id=event_id,
        provision_type=request.provision_type,
        provision_amount=request.provision_amount,
        provision_date=request.provision_date,
        approved_by=request.approved_by
    )


@router.put("/provisions/{provision_id}/release")
async def release_provision(provision_id: UUID, release_amount: Decimal):
    """Release provision"""
    provision = await loss_event_service.release_provision(provision_id, release_amount)
    if not provision:
        raise HTTPException(status_code=404, detail="Provision not found")
    return provision


@router.post("/{event_id}/causality", response_model=LossEventCausality)
async def add_causality(event_id: UUID, request: CausalityRequest):
    """Add causality analysis"""
    return await loss_event_service.add_causality(
        event_id=event_id,
        cause_category=request.cause_category,
        cause_subcategory=request.cause_subcategory,
        cause_description=request.cause_description,
        contributing_factor=request.contributing_factor,
        control_failure=request.control_failure,
        failed_control_id=request.failed_control_id
    )


@router.post("/distribution", response_model=LossDistribution)
async def calculate_distribution(
    event_type: LossEventType,
    period_start: date,
    period_end: date
):
    """Calculate loss distribution"""
    return await loss_event_service.calculate_loss_distribution(
        event_type, period_start, period_end
    )


@router.post("/capital", response_model=OperationalLossCapital)
async def calculate_capital(request: CapitalRequest):
    """Calculate operational risk capital"""
    return await loss_event_service.calculate_operational_capital(
        calculation_date=date.today(),
        methodology=request.methodology,
        business_indicator=request.business_indicator,
        confidence_level=request.confidence_level,
        time_horizon=request.time_horizon
    )


@router.post("/reports", response_model=LossEventReport)
async def generate_report(
    report_period: str,
    period_start: date,
    period_end: date,
    generated_by: str
):
    """Generate loss event report"""
    return await loss_event_service.generate_report(
        report_period, period_start, period_end, generated_by
    )


@router.get("/statistics/summary")
async def get_statistics():
    """Get loss event statistics"""
    return await loss_event_service.get_statistics()
