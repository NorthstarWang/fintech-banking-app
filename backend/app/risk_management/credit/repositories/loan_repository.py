"""Loan Repository - Data access layer for loans"""

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from ..models.loan_models import (
    DelinquencyRecord,
    Loan,
    LoanApplication,
    LoanPayment,
    LoanStatus,
    LoanType,
)


class LoanRepository:
    def __init__(self):
        self._applications: dict[UUID, LoanApplication] = {}
        self._loans: dict[UUID, Loan] = {}
        self._payments: list[LoanPayment] = []
        self._delinquencies: dict[UUID, DelinquencyRecord] = {}
        self._customer_loan_index: dict[str, list[UUID]] = {}
        self._loan_number_index: dict[str, UUID] = {}

    async def save_application(self, application: LoanApplication) -> LoanApplication:
        self._applications[application.application_id] = application
        return application

    async def find_application_by_id(self, application_id: UUID) -> LoanApplication | None:
        return self._applications.get(application_id)

    async def find_applications_by_customer(self, customer_id: str) -> list[LoanApplication]:
        return [a for a in self._applications.values() if a.customer_id == customer_id]

    async def find_applications_by_status(self, status: LoanStatus) -> list[LoanApplication]:
        return [a for a in self._applications.values() if a.status == status]

    async def save_loan(self, loan: Loan) -> Loan:
        self._loans[loan.loan_id] = loan
        self._loan_number_index[loan.loan_number] = loan.loan_id
        if loan.customer_id not in self._customer_loan_index:
            self._customer_loan_index[loan.customer_id] = []
        self._customer_loan_index[loan.customer_id].append(loan.loan_id)
        return loan

    async def find_loan_by_id(self, loan_id: UUID) -> Loan | None:
        return self._loans.get(loan_id)

    async def find_loan_by_number(self, loan_number: str) -> Loan | None:
        loan_id = self._loan_number_index.get(loan_number)
        if loan_id:
            return self._loans.get(loan_id)
        return None

    async def find_loans_by_customer(self, customer_id: str) -> list[Loan]:
        loan_ids = self._customer_loan_index.get(customer_id, [])
        return [self._loans[lid] for lid in loan_ids if lid in self._loans]

    async def find_loans_by_status(self, status: LoanStatus) -> list[Loan]:
        return [l for l in self._loans.values() if l.status == status]

    async def find_loans_by_type(self, loan_type: LoanType) -> list[Loan]:
        return [l for l in self._loans.values() if l.loan_type == loan_type]

    async def find_delinquent_loans(self) -> list[Loan]:
        return [l for l in self._loans.values() if l.status == LoanStatus.DELINQUENT]

    async def find_maturing_loans(self, days: int = 30) -> list[Loan]:
        cutoff = date.today() + timedelta(days=days)
        return [l for l in self._loans.values() if l.maturity_date <= cutoff and l.status == LoanStatus.ACTIVE]

    async def update_loan(self, loan: Loan) -> Loan:
        loan.updated_at = datetime.now(UTC)
        self._loans[loan.loan_id] = loan
        return loan

    async def save_payment(self, payment: LoanPayment) -> LoanPayment:
        self._payments.append(payment)
        return payment

    async def find_payments_by_loan(self, loan_id: UUID) -> list[LoanPayment]:
        return [p for p in self._payments if p.loan_id == loan_id]

    async def save_delinquency(self, record: DelinquencyRecord) -> DelinquencyRecord:
        self._delinquencies[record.record_id] = record
        return record

    async def find_delinquencies_by_loan(self, loan_id: UUID) -> list[DelinquencyRecord]:
        return [d for d in self._delinquencies.values() if d.loan_id == loan_id]

    async def get_portfolio_statistics(self) -> dict[str, Any]:
        total_loans = len(self._loans)
        total_principal = sum(l.principal_amount for l in self._loans.values())
        total_outstanding = sum(l.current_balance for l in self._loans.values())
        by_status = {}
        by_type = {}
        for loan in self._loans.values():
            by_status[loan.status.value] = by_status.get(loan.status.value, 0) + 1
            by_type[loan.loan_type.value] = by_type.get(loan.loan_type.value, 0) + 1
        return {
            "total_loans": total_loans,
            "total_principal": total_principal,
            "total_outstanding": total_outstanding,
            "by_status": by_status,
            "by_type": by_type
        }

    async def count_loans(self) -> int:
        return len(self._loans)


loan_repository = LoanRepository()
