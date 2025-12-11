"""Consumer Protection Compliance API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.consumer_protection_models import (
    ComplaintCategory, ComplaintStatus, FairLendingProtectedClass
)
from ..services.consumer_protection_service import consumer_protection_service

router = APIRouter(prefix="/consumer-protection", tags=["Consumer Protection"])


class ComplaintCreateRequest(BaseModel):
    customer_id: str
    customer_name: str
    contact_method: str
    category: ComplaintCategory
    product_type: str
    description: str
    amount_disputed: Optional[Decimal] = None
    regulatory_complaint: bool = False
    regulator_reference: Optional[str] = None


class ComplaintResolveRequest(BaseModel):
    resolution: str
    resolution_amount: Optional[Decimal] = None
    root_cause: str
    systemic_issue: bool = False


class FairLendingAnalysisRequest(BaseModel):
    analysis_type: str
    product_type: str
    period_start: date
    period_end: date
    protected_class: FairLendingProtectedClass
    total_applications: int
    approved_count: int
    denied_count: int
    control_group_approval_rate: Decimal
    protected_group_approval_rate: Decimal
    analyst: str


class TILADisclosureRequest(BaseModel):
    loan_id: str
    customer_id: str
    disclosure_type: str
    product_type: str
    loan_amount: Decimal
    apr: Decimal
    finance_charge: Decimal
    amount_financed: Decimal
    total_of_payments: Decimal
    payment_amount: Decimal
    payment_frequency: str
    number_of_payments: int
    delivery_method: str


class RESPADisclosureRequest(BaseModel):
    loan_id: str
    disclosure_type: str
    loan_amount: Decimal
    interest_rate: Decimal
    monthly_principal_interest: Decimal
    closing_costs: Decimal
    cash_to_close: Decimal
    origination_charges: Decimal
    delivery_method: str


class UDAPReviewRequest(BaseModel):
    product_service: str
    review_type: str
    reviewer: str
    unfair_assessment: str
    deceptive_assessment: str
    abusive_assessment: str
    issues_identified: List[Dict[str, Any]]
    recommendations: List[str]


class ServicememberProtectionRequest(BaseModel):
    customer_id: str
    account_id: str
    military_status: str
    verification_method: str
    protections_applied: List[str]
    interest_rate_reduction: Optional[Decimal] = None


@router.post("/complaints", response_model=dict)
async def create_complaint(request: ComplaintCreateRequest):
    """Create a new consumer complaint"""
    complaint = await consumer_protection_service.create_complaint(
        customer_id=request.customer_id, customer_name=request.customer_name,
        contact_method=request.contact_method, category=request.category,
        product_type=request.product_type, description=request.description,
        amount_disputed=request.amount_disputed, regulatory_complaint=request.regulatory_complaint,
        regulator_reference=request.regulator_reference
    )
    return {
        "complaint_id": str(complaint.complaint_id),
        "complaint_reference": complaint.complaint_reference,
        "priority": complaint.priority,
        "sla_due_date": str(complaint.sla_due_date)
    }


@router.get("/complaints", response_model=List[dict])
async def list_complaints(
    status: Optional[ComplaintStatus] = None,
    open_only: bool = False,
    regulatory_only: bool = False
):
    """List consumer complaints"""
    if status:
        complaints = await consumer_protection_service.repository.find_complaints_by_status(status)
    elif open_only:
        complaints = await consumer_protection_service.repository.find_open_complaints()
    elif regulatory_only:
        complaints = await consumer_protection_service.repository.find_regulatory_complaints()
    else:
        complaints = await consumer_protection_service.repository.find_all_complaints()
    return [{"complaint_id": str(c.complaint_id), "complaint_reference": c.complaint_reference, "category": c.category.value, "status": c.status.value} for c in complaints]


@router.get("/complaints/{complaint_id}", response_model=dict)
async def get_complaint(complaint_id: UUID):
    """Get a specific complaint"""
    complaint = await consumer_protection_service.repository.find_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "complaint_id": str(complaint.complaint_id),
        "complaint_reference": complaint.complaint_reference,
        "customer_name": complaint.customer_name,
        "category": complaint.category.value,
        "description": complaint.description,
        "status": complaint.status.value,
        "sla_due_date": str(complaint.sla_due_date)
    }


@router.post("/complaints/{complaint_id}/resolve", response_model=dict)
async def resolve_complaint(complaint_id: UUID, request: ComplaintResolveRequest):
    """Resolve a consumer complaint"""
    complaint = await consumer_protection_service.resolve_complaint(
        complaint_id=complaint_id, resolution=request.resolution,
        resolution_amount=request.resolution_amount, root_cause=request.root_cause,
        systemic_issue=request.systemic_issue
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"complaint_id": str(complaint.complaint_id), "status": complaint.status.value}


@router.get("/complaints/customer/{customer_id}", response_model=List[dict])
async def get_customer_complaints(customer_id: str):
    """Get complaints for a specific customer"""
    complaints = await consumer_protection_service.repository.find_complaints_by_customer(customer_id)
    return [{"complaint_id": str(c.complaint_id), "complaint_reference": c.complaint_reference, "status": c.status.value} for c in complaints]


@router.post("/fair-lending/analyze", response_model=dict)
async def perform_fair_lending_analysis(request: FairLendingAnalysisRequest):
    """Perform a fair lending analysis"""
    analysis = await consumer_protection_service.perform_fair_lending_analysis(
        analysis_type=request.analysis_type, product_type=request.product_type,
        period_start=request.period_start, period_end=request.period_end,
        protected_class=request.protected_class, total_applications=request.total_applications,
        approved_count=request.approved_count, denied_count=request.denied_count,
        control_group_approval_rate=request.control_group_approval_rate,
        protected_group_approval_rate=request.protected_group_approval_rate,
        analyst=request.analyst
    )
    return {
        "analysis_id": str(analysis.analysis_id),
        "rate_disparity": float(analysis.rate_disparity),
        "statistical_significance": analysis.statistical_significance
    }


@router.get("/fair-lending", response_model=List[dict])
async def list_fair_lending_analyses(
    with_findings_only: bool = False,
    protected_class: Optional[str] = None
):
    """List fair lending analyses"""
    if with_findings_only:
        analyses = await consumer_protection_service.repository.find_fair_lending_with_findings()
    elif protected_class:
        analyses = await consumer_protection_service.repository.find_fair_lending_by_protected_class(protected_class)
    else:
        analyses = await consumer_protection_service.repository.find_all_fair_lending()
    return [{"analysis_id": str(a.analysis_id), "product_type": a.product_type, "protected_class": a.protected_class.value, "statistical_significance": a.statistical_significance} for a in analyses]


@router.post("/tila-disclosures", response_model=dict)
async def create_tila_disclosure(request: TILADisclosureRequest):
    """Create a TILA disclosure"""
    disclosure = await consumer_protection_service.create_tila_disclosure(
        loan_id=request.loan_id, customer_id=request.customer_id,
        disclosure_type=request.disclosure_type, product_type=request.product_type,
        loan_amount=request.loan_amount, apr=request.apr, finance_charge=request.finance_charge,
        amount_financed=request.amount_financed, total_of_payments=request.total_of_payments,
        payment_amount=request.payment_amount, payment_frequency=request.payment_frequency,
        number_of_payments=request.number_of_payments, delivery_method=request.delivery_method
    )
    return {"disclosure_id": str(disclosure.disclosure_id), "loan_id": disclosure.loan_id}


@router.get("/tila-disclosures/loan/{loan_id}", response_model=List[dict])
async def get_loan_tila_disclosures(loan_id: str):
    """Get TILA disclosures for a loan"""
    disclosures = await consumer_protection_service.repository.find_tila_by_loan(loan_id)
    return [{"disclosure_id": str(d.disclosure_id), "disclosure_type": d.disclosure_type, "apr": float(d.apr)} for d in disclosures]


@router.post("/respa-disclosures", response_model=dict)
async def create_respa_disclosure(request: RESPADisclosureRequest):
    """Create a RESPA disclosure"""
    disclosure = await consumer_protection_service.create_respa_disclosure(
        loan_id=request.loan_id, disclosure_type=request.disclosure_type,
        loan_amount=request.loan_amount, interest_rate=request.interest_rate,
        monthly_principal_interest=request.monthly_principal_interest,
        closing_costs=request.closing_costs, cash_to_close=request.cash_to_close,
        origination_charges=request.origination_charges, delivery_method=request.delivery_method
    )
    return {"disclosure_id": str(disclosure.disclosure_id), "loan_id": disclosure.loan_id}


@router.get("/respa-disclosures/loan/{loan_id}", response_model=List[dict])
async def get_loan_respa_disclosures(loan_id: str):
    """Get RESPA disclosures for a loan"""
    disclosures = await consumer_protection_service.repository.find_respa_by_loan(loan_id)
    return [{"disclosure_id": str(d.disclosure_id), "disclosure_type": d.disclosure_type, "closing_costs": float(d.closing_costs)} for d in disclosures]


@router.post("/udap-reviews", response_model=dict)
async def perform_udap_review(request: UDAPReviewRequest):
    """Perform a UDAP review"""
    review = await consumer_protection_service.perform_udap_review(
        product_service=request.product_service, review_type=request.review_type,
        reviewer=request.reviewer, unfair_assessment=request.unfair_assessment,
        deceptive_assessment=request.deceptive_assessment, abusive_assessment=request.abusive_assessment,
        issues_identified=request.issues_identified, recommendations=request.recommendations
    )
    return {
        "review_id": str(review.review_id),
        "risk_rating": review.risk_rating,
        "remediation_required": review.remediation_required
    }


@router.get("/udap-reviews", response_model=List[dict])
async def list_udap_reviews(requiring_remediation: bool = False, high_risk_only: bool = False):
    """List UDAP reviews"""
    if requiring_remediation:
        reviews = await consumer_protection_service.repository.find_udap_requiring_remediation()
    elif high_risk_only:
        reviews = await consumer_protection_service.repository.find_high_risk_udap()
    else:
        reviews = await consumer_protection_service.repository.find_all_udap()
    return [{"review_id": str(r.review_id), "product_service": r.product_service, "risk_rating": r.risk_rating} for r in reviews]


@router.post("/servicemember-protections", response_model=dict)
async def register_servicemember_protection(request: ServicememberProtectionRequest):
    """Register servicemember protection"""
    protection = await consumer_protection_service.register_servicemember(
        customer_id=request.customer_id, account_id=request.account_id,
        military_status=request.military_status, verification_method=request.verification_method,
        protections_applied=request.protections_applied, interest_rate_reduction=request.interest_rate_reduction
    )
    return {
        "protection_id": str(protection.protection_id),
        "scra_benefits_applied": protection.scra_benefits_applied,
        "mla_benefits_applied": protection.mla_benefits_applied
    }


@router.get("/servicemember-protections/{customer_id}", response_model=List[dict])
async def get_customer_servicemember_protections(customer_id: str):
    """Get servicemember protections for a customer"""
    protections = await consumer_protection_service.repository.find_servicemember_by_customer(customer_id)
    return [{"protection_id": str(p.protection_id), "military_status": p.military_status, "protections_applied": p.protections_applied} for p in protections]


@router.get("/servicemember-protections", response_model=List[dict])
async def list_active_servicemember_protections():
    """List all active servicemember protections"""
    protections = await consumer_protection_service.repository.find_active_servicemember_protections()
    return [{"protection_id": str(p.protection_id), "customer_id": p.customer_id, "military_status": p.military_status} for p in protections]


@router.post("/reports/generate", response_model=dict)
async def generate_consumer_protection_report(reporting_period: str = Query(...), generated_by: str = Query(...)):
    """Generate a consumer protection compliance report"""
    report = await consumer_protection_service.generate_report(
        reporting_period=reporting_period, generated_by=generated_by
    )
    return {"report_id": str(report.report_id), "report_date": str(report.report_date)}


@router.get("/statistics", response_model=dict)
async def get_consumer_protection_statistics():
    """Get consumer protection statistics"""
    return await consumer_protection_service.get_statistics()
