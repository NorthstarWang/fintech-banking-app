"""Loan Service - Loan origination and risk management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from ..models.loan_models import (
    LoanApplication, LoanRiskAssessment, Loan, LoanPayment,
    DelinquencyRecord, LoanStatistics, LoanType, LoanStatus, RiskDecision
)


class LoanService:
    def __init__(self):
        self._applications: Dict[UUID, LoanApplication] = {}
        self._assessments: Dict[UUID, LoanRiskAssessment] = {}
        self._loans: Dict[UUID, Loan] = {}
        self._payments: List[LoanPayment] = []
        self._delinquencies: Dict[UUID, DelinquencyRecord] = {}
        self._counter = 0

    def _generate_number(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    async def submit_application(
        self, customer_id: str, customer_name: str, loan_type: LoanType,
        requested_amount: float, requested_term: int, purpose: str,
        annual_income: float, monthly_debt: float
    ) -> LoanApplication:
        dti = (monthly_debt / (annual_income / 12)) * 100 if annual_income > 0 else 100

        application = LoanApplication(
            application_number=self._generate_number("APP"),
            customer_id=customer_id,
            customer_name=customer_name,
            loan_type=loan_type,
            requested_amount=requested_amount,
            requested_term_months=requested_term,
            purpose=purpose,
            employment_status="employed",
            annual_income=annual_income,
            monthly_debt=monthly_debt,
            debt_to_income_ratio=dti
        )
        self._applications[application.application_id] = application
        return application

    async def get_application(self, application_id: UUID) -> Optional[LoanApplication]:
        return self._applications.get(application_id)

    async def assess_application(self, application_id: UUID, assessed_by: str) -> Optional[LoanRiskAssessment]:
        application = self._applications.get(application_id)
        if not application:
            return None

        # Calculate risk score
        risk_score = 50.0
        if application.debt_to_income_ratio > 43:
            risk_score += 20
        if application.requested_amount > 50000:
            risk_score += 10
        if application.credit_score and application.credit_score < 650:
            risk_score += 25

        risk_grade = "A" if risk_score < 30 else "B" if risk_score < 50 else "C" if risk_score < 70 else "D"
        pd = risk_score / 1000
        lgd = 0.45
        expected_loss = application.requested_amount * pd * lgd

        decision = RiskDecision.APPROVE if risk_score < 50 else (
            RiskDecision.CONDITIONAL_APPROVE if risk_score < 70 else RiskDecision.DECLINE
        )

        assessment = LoanRiskAssessment(
            application_id=application_id,
            customer_id=application.customer_id,
            risk_score=risk_score,
            risk_grade=risk_grade,
            probability_of_default=pd,
            loss_given_default=lgd,
            expected_loss=expected_loss,
            recommended_decision=decision,
            assessed_by=assessed_by
        )

        self._assessments[assessment.assessment_id] = assessment
        application.risk_assessment = assessment.model_dump()
        application.status = LoanStatus.UNDER_REVIEW

        return assessment

    async def make_decision(
        self, application_id: UUID, decision: RiskDecision,
        reason: str, conditions: List[str] = None
    ) -> Optional[LoanApplication]:
        application = self._applications.get(application_id)
        if not application:
            return None

        application.decision = decision
        application.decision_date = datetime.utcnow()
        application.decision_reason = reason
        application.conditions = conditions or []
        application.status = LoanStatus.APPROVED if decision == RiskDecision.APPROVE else (
            LoanStatus.REJECTED if decision == RiskDecision.DECLINE else LoanStatus.UNDER_REVIEW
        )
        return application

    async def fund_loan(self, application_id: UUID) -> Optional[Loan]:
        application = self._applications.get(application_id)
        if not application or application.decision != RiskDecision.APPROVE:
            return None

        today = date.today()
        monthly_rate = 0.05 / 12
        monthly_payment = application.requested_amount * (
            monthly_rate * (1 + monthly_rate) ** application.requested_term_months
        ) / ((1 + monthly_rate) ** application.requested_term_months - 1)

        loan = Loan(
            loan_number=self._generate_number("LN"),
            application_id=application_id,
            customer_id=application.customer_id,
            customer_name=application.customer_name,
            loan_type=application.loan_type,
            principal_amount=application.requested_amount,
            current_balance=application.requested_amount,
            interest_rate=0.05,
            term_months=application.requested_term_months,
            monthly_payment=monthly_payment,
            origination_date=today,
            maturity_date=today + timedelta(days=30 * application.requested_term_months),
            first_payment_date=today + timedelta(days=30),
            next_payment_date=today + timedelta(days=30)
        )

        self._loans[loan.loan_id] = loan
        application.status = LoanStatus.FUNDED
        return loan

    async def get_loan(self, loan_id: UUID) -> Optional[Loan]:
        return self._loans.get(loan_id)

    async def record_payment(
        self, loan_id: UUID, payment_amount: float, payment_method: str
    ) -> Optional[LoanPayment]:
        loan = self._loans.get(loan_id)
        if not loan:
            return None

        payment_number = loan.total_payments_made + 1
        interest_portion = loan.current_balance * (loan.interest_rate / 12)
        principal_portion = min(payment_amount - interest_portion, loan.current_balance)

        payment = LoanPayment(
            loan_id=loan_id,
            payment_number=payment_number,
            payment_date=date.today(),
            due_date=loan.next_payment_date or date.today(),
            scheduled_amount=loan.monthly_payment,
            actual_amount=payment_amount,
            principal_portion=principal_portion,
            interest_portion=interest_portion,
            balance_after=loan.current_balance - principal_portion,
            payment_method=payment_method
        )

        loan.current_balance -= principal_portion
        loan.total_payments_made += 1
        loan.total_principal_paid += principal_portion
        loan.total_interest_paid += interest_portion
        loan.last_payment_date = date.today()
        loan.next_payment_date = date.today() + timedelta(days=30)

        if loan.current_balance <= 0:
            loan.status = LoanStatus.PAID_OFF

        self._payments.append(payment)
        return payment

    async def record_delinquency(self, loan_id: UUID, amount_past_due: float) -> Optional[DelinquencyRecord]:
        loan = self._loans.get(loan_id)
        if not loan:
            return None

        days = loan.days_past_due
        bucket = "30" if days <= 30 else "60" if days <= 60 else "90" if days <= 90 else "120+"

        record = DelinquencyRecord(
            loan_id=loan_id,
            customer_id=loan.customer_id,
            delinquency_start_date=date.today() - timedelta(days=days),
            days_delinquent=days,
            amount_past_due=amount_past_due,
            delinquency_bucket=bucket
        )

        loan.status = LoanStatus.DELINQUENT
        self._delinquencies[record.record_id] = record
        return record

    async def get_customer_loans(self, customer_id: str) -> List[Loan]:
        return [l for l in self._loans.values() if l.customer_id == customer_id]

    async def get_delinquent_loans(self) -> List[Loan]:
        return [l for l in self._loans.values() if l.status == LoanStatus.DELINQUENT]

    async def get_statistics(self) -> LoanStatistics:
        stats = LoanStatistics(
            total_loans=len(self._loans),
            total_principal=sum(l.principal_amount for l in self._loans.values()),
            total_outstanding=sum(l.current_balance for l in self._loans.values())
        )
        for loan in self._loans.values():
            stats.by_status[loan.status.value] = stats.by_status.get(loan.status.value, 0) + 1
            stats.by_type[loan.loan_type.value] = stats.by_type.get(loan.loan_type.value, 0) + 1
        if self._loans:
            stats.average_interest_rate = sum(l.interest_rate for l in self._loans.values()) / len(self._loans)
        return stats


loan_service = LoanService()
