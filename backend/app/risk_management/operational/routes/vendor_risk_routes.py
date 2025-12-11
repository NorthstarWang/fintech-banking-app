"""Vendor Risk Routes - API endpoints for third-party risk management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.vendor_risk_models import (
    Vendor, VendorContract, VendorAssessment, VendorDueDiligence,
    VendorIncident, VendorPerformance, VendorRiskMetrics,
    VendorTier, VendorStatus, ServiceCategory, RiskRating, AssessmentType
)
from ..services.vendor_risk_service import vendor_risk_service

router = APIRouter(prefix="/vendors", tags=["Vendor Risk"])


class RegisterVendorRequest(BaseModel):
    vendor_name: str
    legal_name: str
    service_category: ServiceCategory
    services_provided: List[str]
    primary_contact: str
    contact_email: str
    contact_phone: str
    address: str
    country: str
    relationship_owner: str
    business_unit: str
    annual_spend: Decimal = Decimal("0")
    payment_terms: str = "Net 30"
    data_access: bool = False
    pii_access: bool = False
    system_access: bool = False
    critical_vendor: bool = False


class CreateContractRequest(BaseModel):
    contract_number: str
    contract_name: str
    contract_type: str
    effective_date: date
    expiration_date: date
    contract_value: Decimal
    currency: str
    payment_frequency: str
    termination_notice_days: int
    owner: str
    approved_by: str
    document_location: str
    auto_renewal: bool = False
    sla_attached: bool = False
    audit_rights: bool = False


class PerformAssessmentRequest(BaseModel):
    assessment_type: AssessmentType
    assessor: str
    financial_risk_rating: RiskRating
    operational_risk_rating: RiskRating
    compliance_risk_rating: RiskRating
    security_risk_rating: RiskRating
    reputational_risk_rating: RiskRating
    financial_stability: str
    years_in_business: int
    certifications: List[str]
    audit_reports: List[str]
    insurance_coverage: Dict[str, Decimal]
    findings: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class InitiateDDRequest(BaseModel):
    due_diligence_type: str
    performed_by: str
    background_check: bool = True
    financial_review: bool = True
    reference_check: bool = True
    security_assessment: bool = True
    compliance_verification: bool = True
    sanctions_screening: bool = True
    adverse_media_check: bool = True


class ReportIncidentRequest(BaseModel):
    incident_type: str
    severity: str
    description: str
    impact_description: str
    service_affected: str
    sla_breached: bool = False


class RecordPerformanceRequest(BaseModel):
    review_period: str
    period_start: date
    period_end: date
    sla_metrics: Dict[str, Decimal]
    quality_score: Decimal
    delivery_score: Decimal
    responsiveness_score: Decimal
    cost_performance: Decimal
    issues_reported: int
    issues_resolved: int
    strengths: List[str]
    areas_for_improvement: List[str]
    reviewer: str


@router.post("/", response_model=Vendor)
async def register_vendor(request: RegisterVendorRequest):
    """Register new vendor"""
    return await vendor_risk_service.register_vendor(
        vendor_name=request.vendor_name,
        legal_name=request.legal_name,
        service_category=request.service_category,
        services_provided=request.services_provided,
        primary_contact=request.primary_contact,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone,
        address=request.address,
        country=request.country,
        relationship_owner=request.relationship_owner,
        business_unit=request.business_unit,
        annual_spend=request.annual_spend,
        payment_terms=request.payment_terms,
        data_access=request.data_access,
        pii_access=request.pii_access,
        system_access=request.system_access,
        critical_vendor=request.critical_vendor
    )


@router.get("/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: UUID):
    """Get vendor by ID"""
    vendor = await vendor_risk_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.get("/", response_model=List[Vendor])
async def list_vendors(
    status: Optional[VendorStatus] = Query(None),
    tier: Optional[VendorTier] = Query(None),
    category: Optional[ServiceCategory] = Query(None),
    critical_only: bool = Query(False)
):
    """List vendors"""
    return await vendor_risk_service.list_vendors(status, tier, category, critical_only)


@router.put("/{vendor_id}/status", response_model=Vendor)
async def update_status(vendor_id: UUID, new_status: VendorStatus):
    """Update vendor status"""
    vendor = await vendor_risk_service.update_vendor_status(vendor_id, new_status)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("/{vendor_id}/contracts", response_model=VendorContract)
async def create_contract(vendor_id: UUID, request: CreateContractRequest):
    """Create vendor contract"""
    return await vendor_risk_service.create_contract(
        vendor_id=vendor_id,
        contract_number=request.contract_number,
        contract_name=request.contract_name,
        contract_type=request.contract_type,
        effective_date=request.effective_date,
        expiration_date=request.expiration_date,
        contract_value=request.contract_value,
        currency=request.currency,
        payment_frequency=request.payment_frequency,
        termination_notice_days=request.termination_notice_days,
        owner=request.owner,
        approved_by=request.approved_by,
        document_location=request.document_location,
        auto_renewal=request.auto_renewal,
        sla_attached=request.sla_attached,
        audit_rights=request.audit_rights
    )


@router.get("/{vendor_id}/contracts", response_model=List[VendorContract])
async def get_contracts(vendor_id: UUID):
    """Get vendor contracts"""
    return await vendor_risk_service.get_vendor_contracts(vendor_id)


@router.get("/contracts/expiring", response_model=List[VendorContract])
async def get_expiring_contracts(days: int = Query(90)):
    """Get contracts expiring soon"""
    return await vendor_risk_service.get_expiring_contracts(days)


@router.post("/{vendor_id}/assessments", response_model=VendorAssessment)
async def perform_assessment(vendor_id: UUID, request: PerformAssessmentRequest):
    """Perform vendor assessment"""
    return await vendor_risk_service.perform_assessment(
        vendor_id=vendor_id,
        assessment_type=request.assessment_type,
        assessor=request.assessor,
        financial_risk_rating=request.financial_risk_rating,
        operational_risk_rating=request.operational_risk_rating,
        compliance_risk_rating=request.compliance_risk_rating,
        security_risk_rating=request.security_risk_rating,
        reputational_risk_rating=request.reputational_risk_rating,
        financial_stability=request.financial_stability,
        years_in_business=request.years_in_business,
        certifications=request.certifications,
        audit_reports=request.audit_reports,
        insurance_coverage=request.insurance_coverage,
        findings=request.findings,
        recommendations=request.recommendations
    )


@router.get("/{vendor_id}/assessments", response_model=List[VendorAssessment])
async def get_assessments(vendor_id: UUID):
    """Get vendor assessments"""
    return await vendor_risk_service.get_vendor_assessments(vendor_id)


@router.post("/{vendor_id}/due-diligence", response_model=VendorDueDiligence)
async def initiate_due_diligence(vendor_id: UUID, request: InitiateDDRequest):
    """Initiate due diligence"""
    return await vendor_risk_service.initiate_due_diligence(
        vendor_id=vendor_id,
        due_diligence_type=request.due_diligence_type,
        performed_by=request.performed_by,
        background_check=request.background_check,
        financial_review=request.financial_review,
        reference_check=request.reference_check,
        security_assessment=request.security_assessment,
        compliance_verification=request.compliance_verification,
        sanctions_screening=request.sanctions_screening,
        adverse_media_check=request.adverse_media_check
    )


@router.post("/{vendor_id}/incidents", response_model=VendorIncident)
async def report_incident(vendor_id: UUID, request: ReportIncidentRequest):
    """Report vendor incident"""
    return await vendor_risk_service.report_incident(
        vendor_id=vendor_id,
        incident_type=request.incident_type,
        severity=request.severity,
        description=request.description,
        impact_description=request.impact_description,
        service_affected=request.service_affected,
        sla_breached=request.sla_breached
    )


@router.get("/{vendor_id}/incidents", response_model=List[VendorIncident])
async def get_incidents(vendor_id: UUID):
    """Get vendor incidents"""
    return await vendor_risk_service.get_vendor_incidents(vendor_id)


@router.post("/{vendor_id}/performance", response_model=VendorPerformance)
async def record_performance(vendor_id: UUID, request: RecordPerformanceRequest):
    """Record vendor performance"""
    return await vendor_risk_service.record_performance(
        vendor_id=vendor_id,
        review_period=request.review_period,
        period_start=request.period_start,
        period_end=request.period_end,
        sla_metrics=request.sla_metrics,
        quality_score=request.quality_score,
        delivery_score=request.delivery_score,
        responsiveness_score=request.responsiveness_score,
        cost_performance=request.cost_performance,
        issues_reported=request.issues_reported,
        issues_resolved=request.issues_resolved,
        strengths=request.strengths,
        areas_for_improvement=request.areas_for_improvement,
        reviewer=request.reviewer
    )


@router.get("/{vendor_id}/performance", response_model=List[VendorPerformance])
async def get_performance(vendor_id: UUID):
    """Get vendor performance"""
    return await vendor_risk_service.get_vendor_performance(vendor_id)


@router.get("/metrics/summary", response_model=VendorRiskMetrics)
async def get_metrics():
    """Get vendor risk metrics"""
    return await vendor_risk_service.generate_metrics()


@router.get("/statistics")
async def get_statistics():
    """Get vendor statistics"""
    return await vendor_risk_service.get_statistics()
