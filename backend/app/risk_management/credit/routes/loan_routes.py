"""Loan Routes - API endpoints for loan management"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.loan_models import (
    LoanApplication, Loan, LoanPayment, LoanType, LoanStatus, RiskDecision
)
from ..services.loan_service import loan_service

router = APIRouter(prefix="/credit/loans", tags=["Credit Loans"])


class SubmitApplicationRequest(BaseModel):
    customer_id: str
    customer_name: str
    loan_type: LoanType
    requested_amount: float = Field(gt=0)
    requested_term: int = Field(gt=0, le=360)
    purpose: str
    annual_income: float = Field(gt=0)
    monthly_debt: float = Field(ge=0)


class MakeDecisionRequest(BaseModel):
    decision: RiskDecision
    reason: str
    conditions: List[str] = []


class RecordPaymentRequest(BaseModel):
    payment_amount: float = Field(gt=0)
    payment_method: str


@router.post("/applications", response_model=LoanApplication)
async def submit_application(request: SubmitApplicationRequest):
    """Submit a loan application"""
    application = await loan_service.submit_application(
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        loan_type=request.loan_type,
        requested_amount=request.requested_amount,
        requested_term=request.requested_term,
        purpose=request.purpose,
        annual_income=request.annual_income,
        monthly_debt=request.monthly_debt
    )
    return application


@router.get("/applications/{application_id}", response_model=LoanApplication)
async def get_application(application_id: UUID):
    """Get loan application by ID"""
    application = await loan_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("/applications/{application_id}/assess")
async def assess_application(application_id: UUID, assessed_by: str):
    """Assess a loan application"""
    assessment = await loan_service.assess_application(application_id, assessed_by)
    if not assessment:
        raise HTTPException(status_code=404, detail="Application not found")
    return assessment


@router.post("/applications/{application_id}/decision", response_model=LoanApplication)
async def make_decision(application_id: UUID, request: MakeDecisionRequest):
    """Make a decision on loan application"""
    application = await loan_service.make_decision(
        application_id, request.decision, request.reason, request.conditions
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("/applications/{application_id}/fund", response_model=Loan)
async def fund_loan(application_id: UUID):
    """Fund an approved loan"""
    loan = await loan_service.fund_loan(application_id)
    if not loan:
        raise HTTPException(status_code=400, detail="Cannot fund loan - not approved")
    return loan


@router.get("/{loan_id}", response_model=Loan)
async def get_loan(loan_id: UUID):
    """Get loan by ID"""
    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.post("/{loan_id}/payments", response_model=LoanPayment)
async def record_payment(loan_id: UUID, request: RecordPaymentRequest):
    """Record a loan payment"""
    payment = await loan_service.record_payment(
        loan_id, request.payment_amount, request.payment_method
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Loan not found")
    return payment


@router.get("/customer/{customer_id}", response_model=List[Loan])
async def get_customer_loans(customer_id: str):
    """Get all loans for a customer"""
    return await loan_service.get_customer_loans(customer_id)


@router.get("/delinquent", response_model=List[Loan])
async def get_delinquent_loans():
    """Get all delinquent loans"""
    return await loan_service.get_delinquent_loans()


@router.get("/")
async def list_loans(
    status: Optional[LoanStatus] = None,
    loan_type: Optional[LoanType] = None,
    limit: int = Query(default=100, le=500)
):
    """List loans with optional filters"""
    return {"loans": []}


@router.get("/statistics/summary")
async def get_loan_statistics():
    """Get loan statistics"""
    return await loan_service.get_statistics()
