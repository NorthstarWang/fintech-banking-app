"""
Loan management system repository with in-memory storage.
"""
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from app.models.entities.loan_models import (
    InterestType,
    LoanAmortizationRequest,
    LoanApplicationCreate,
    LoanApplicationResponse,
    LoanOfferResponse,
    LoanPaymentCreate,
    LoanPaymentResponse,
    LoanPaymentScheduleResponse,
    LoanRefinanceAnalysis,
    LoanResponse,
    LoanStatus,
    LoanSummaryStats,
    PaymentFrequency,
)


class LoanManager:
    """Manager for loan-related data and operations."""

    def __init__(self, data_manager):
        self.data_manager = data_manager

        # Initialize loan-specific stores if not present
        if not hasattr(self.data_manager, 'loan_applications'):
            self.data_manager.loan_applications = []
        if not hasattr(self.data_manager, 'loan_offers'):
            self.data_manager.loan_offers = []
        if not hasattr(self.data_manager, 'loans'):
            self.data_manager.loans = []
        if not hasattr(self.data_manager, 'loan_payments'):
            self.data_manager.loan_payments = []
        if not hasattr(self.data_manager, 'loan_payment_schedules'):
            self.data_manager.loan_payment_schedules = []

    # Application Management
    def create_application(self, user_id: int, application: LoanApplicationCreate) -> LoanApplicationResponse:
        """Create a new loan application."""
        # Get user's credit score (mock for now)
        credit_score = self._get_user_credit_score(user_id)

        # Calculate debt-to-income ratio
        dti_ratio = self._calculate_dti_ratio(
            user_id,
            application.annual_income,
            application.monthly_expenses
        )

        app_data = {
            'id': len(self.data_manager.loan_applications) + 1,
            'user_id': user_id,
            'loan_type': application.loan_type,
            'requested_amount': application.requested_amount,
            'purpose': application.purpose,
            'term_months': application.term_months,
            'status': LoanStatus.APPLICATION,
            'credit_score_at_application': credit_score,
            'annual_income': application.annual_income,
            'debt_to_income_ratio': dti_ratio,
            'employment_status': application.employment_status,
            'monthly_expenses': application.monthly_expenses,
            'collateral_description': application.collateral_description,
            'collateral_value': application.collateral_value,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'decision_date': None,
            'rejection_reason': None
        }

        self.data_manager.loan_applications.append(app_data)
        return LoanApplicationResponse(**app_data)

    def get_user_applications(self, user_id: int) -> list[LoanApplicationResponse]:
        """Get all loan applications for a user."""
        apps = []
        for app in self.data_manager.loan_applications:
            if app['user_id'] == user_id:
                # Map the mock data to the expected format
                app_data = app.copy()

                # Map status values
                if app_data.get('status') == 'pending':
                    app_data['status'] = LoanStatus.PENDING_APPROVAL
                elif app_data.get('status') == 'approved':
                    app_data['status'] = LoanStatus.APPROVED
                elif app_data.get('status') == 'rejected':
                    app_data['status'] = LoanStatus.APPLICATION

                # Add missing required fields with defaults
                if 'credit_score_at_application' not in app_data:
                    app_data['credit_score_at_application'] = 700  # Default credit score

                if 'debt_to_income_ratio' not in app_data:
                    # Calculate based on monthly expenses and income
                    monthly_income = app_data.get('annual_income', 60000) / 12
                    monthly_expenses = app_data.get('monthly_expenses', 2000)
                    app_data['debt_to_income_ratio'] = round(monthly_expenses / monthly_income, 2)

                if 'updated_at' not in app_data:
                    app_data['updated_at'] = app_data.get('created_at', datetime.utcnow())

                # Ensure loan_type is lowercase (to match enum values)
                if 'loan_type' in app_data and isinstance(app_data['loan_type'], str):
                    app_data['loan_type'] = app_data['loan_type'].lower()

                try:
                    apps.append(LoanApplicationResponse(**app_data))
                except Exception:
                    continue

        return sorted(apps, key=lambda x: x.created_at, reverse=True)

    def process_application(self, application_id: int) -> list[LoanOfferResponse]:
        """Process application and generate offers."""
        app = self._get_application(application_id)
        if not app:
            return []

        # Update application status
        app['status'] = LoanStatus.PENDING_APPROVAL
        app['updated_at'] = datetime.utcnow()

        # Generate offers based on credit score and loan type
        offers = self._generate_loan_offers(app)

        # Update application status based on offers
        if offers:
            app['status'] = LoanStatus.APPROVED
            app['decision_date'] = datetime.utcnow()
        else:
            app['status'] = LoanStatus.APPLICATION
            app['rejection_reason'] = "Does not meet minimum requirements"
            app['decision_date'] = datetime.utcnow()

        return offers

    # Loan Management
    def accept_offer(self, offer_id: int, user_id: int) -> LoanResponse:
        """Accept a loan offer and create an active loan."""
        offer = self._get_offer(offer_id)
        if not offer:
            raise ValueError("Offer not found")

        app = self._get_application(offer['application_id'])
        if app['user_id'] != user_id:
            raise ValueError("Unauthorized")

        # Create account for the loan
        account_id = self._create_loan_account(user_id, offer)

        # Create loan record
        loan_data = {
            'id': len(self.data_manager.loans) + 1,
            'user_id': user_id,
            'account_id': account_id,
            'offer_id': offer_id,
            'application_id': offer['application_id'],
            'loan_type': app['loan_type'],
            'lender_name': offer['lender_name'],
            'original_amount': offer['approved_amount'],
            'current_balance': offer['approved_amount'],
            'interest_rate': offer['interest_rate'],
            'interest_type': offer['interest_type'],
            'term_months': offer['term_months'],
            'payment_frequency': PaymentFrequency.MONTHLY,
            'monthly_payment': offer['monthly_payment'],
            'next_payment_date': self._calculate_next_payment_date(),
            'next_payment_amount': offer['monthly_payment'],
            'payments_made': 0,
            'payments_remaining': offer['term_months'],
            'total_paid': 0.0,
            'total_interest_paid': 0.0,
            'status': LoanStatus.ACTIVE,
            'originated_date': date.today(),
            'maturity_date': self._calculate_maturity_date(offer['term_months']),
            'last_payment_date': None,
            'escrow_balance': None,
            'collateral_description': app.get('collateral_description'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        self.data_manager.loans.append(loan_data)

        # Generate payment schedule
        self._generate_payment_schedule(loan_data)

        return LoanResponse(**loan_data)

    def get_user_loans(self, user_id: int, status: LoanStatus | None = None) -> list[LoanResponse]:
        """Get all loans for a user."""
        loans = [
            LoanResponse(**loan)
            for loan in self.data_manager.loans
            if loan['user_id'] == user_id and (status is None or loan['status'] == status)
        ]
        return sorted(loans, key=lambda x: x.created_at, reverse=True)

    def get_loan_details(self, loan_id: int, user_id: int) -> LoanResponse | None:
        """Get detailed information about a specific loan."""
        loan = self._get_loan(loan_id)
        if loan and loan['user_id'] == user_id:
            return LoanResponse(**loan)
        return None

    # Payment Management
    def make_payment(self, payment: LoanPaymentCreate, user_id: int) -> LoanPaymentResponse:
        """Process a loan payment."""
        loan = self._get_loan(payment.loan_id)
        if not loan or loan['user_id'] != user_id:
            raise ValueError("Loan not found or unauthorized")

        if loan['status'] != LoanStatus.ACTIVE:
            raise ValueError("Loan is not active")

        # Calculate payment allocation
        payment_date = payment.payment_date or date.today()
        payment_number = loan['payments_made'] + 1

        # Get scheduled payment info
        scheduled = self._get_scheduled_payment(loan['id'], payment_number)
        interest_amount = scheduled['interest'] if scheduled else 0

        # Allocate payment
        if payment.payment_type == "payoff":
            principal_amount = loan['current_balance']
            interest_amount = self._calculate_payoff_interest(loan, payment_date)
            total_amount = principal_amount + interest_amount
        else:
            principal_amount = payment.amount - interest_amount
            if payment.payment_type == "extra_principal":
                principal_amount = payment.amount  # All goes to principal
                interest_amount = 0

        # Create payment record
        payment_data = {
            'id': len(self.data_manager.loan_payments) + 1,
            'loan_id': loan['id'],
            'payment_number': payment_number,
            'amount': payment.amount,
            'principal_amount': principal_amount,
            'interest_amount': interest_amount,
            'escrow_amount': None,
            'extra_principal': max(0, principal_amount - (scheduled['principal'] if scheduled else 0)),
            'payment_type': payment.payment_type,
            'payment_date': payment_date,
            'posted_date': datetime.utcnow(),
            'remaining_balance': loan['current_balance'] - principal_amount,
            'note': payment.note
        }

        self.data_manager.loan_payments.append(payment_data)

        # Update loan
        loan['current_balance'] = payment_data['remaining_balance']
        loan['payments_made'] += 1
        loan['payments_remaining'] = max(0, loan['payments_remaining'] - 1)
        loan['total_paid'] += payment.amount
        loan['total_interest_paid'] += interest_amount
        loan['last_payment_date'] = payment_date
        loan['next_payment_date'] = self._calculate_next_payment_date(payment_date)
        loan['updated_at'] = datetime.utcnow()

        # Check if loan is paid off
        if loan['current_balance'] <= 0:
            loan['status'] = LoanStatus.PAID_OFF
            loan['current_balance'] = 0

        return LoanPaymentResponse(**payment_data)

    def get_payment_history(self, loan_id: int, user_id: int) -> list[LoanPaymentResponse]:
        """Get payment history for a loan."""
        loan = self._get_loan(loan_id)
        if not loan or loan['user_id'] != user_id:
            return []

        payments = [
            LoanPaymentResponse(**payment)
            for payment in self.data_manager.loan_payments
            if payment['loan_id'] == loan_id
        ]
        return sorted(payments, key=lambda x: x.payment_date, reverse=True)

    def get_payment_schedule(self, loan_id: int, user_id: int) -> list[LoanPaymentScheduleResponse]:
        """Get payment schedule for a loan."""
        loan = self._get_loan(loan_id)
        if not loan or loan['user_id'] != user_id:
            return []

        schedule = [
            LoanPaymentScheduleResponse(**sched)
            for sched in self.data_manager.loan_payment_schedules
            if sched['loan_id'] == loan_id
        ]
        return sorted(schedule, key=lambda x: x.payment_number)

    # Analytics and Tools
    def calculate_amortization(self, request: LoanAmortizationRequest) -> list[LoanPaymentScheduleResponse]:
        """Calculate loan amortization schedule."""
        schedule = []
        remaining_balance = request.principal
        monthly_rate = request.interest_rate / 100 / 12
        monthly_payment = self._calculate_monthly_payment(
            request.principal,
            request.interest_rate,
            request.term_months
        )

        cumulative_interest = 0
        cumulative_principal = 0
        payment_date = request.start_date or date.today()

        for i in range(1, request.term_months + 1):
            interest = remaining_balance * monthly_rate
            principal = monthly_payment - interest

            # Apply extra payment if specified
            if request.extra_payment and request.extra_payment > 0:
                if request.extra_payment_frequency == "monthly" or not request.extra_payment_frequency:
                    principal += request.extra_payment

            remaining_balance -= principal
            cumulative_interest += interest
            cumulative_principal += principal

            if i < request.term_months:
                payment_date = self._add_months(payment_date, 1)

            schedule.append(LoanPaymentScheduleResponse(
                payment_number=i,
                payment_date=payment_date,
                payment_amount=monthly_payment + (request.extra_payment or 0),
                principal=principal,
                interest=interest,
                remaining_balance=max(0, remaining_balance),
                cumulative_interest=cumulative_interest,
                cumulative_principal=cumulative_principal
            ))

            if remaining_balance <= 0:
                break

        return schedule

    def analyze_refinance(self, loan_id: int, user_id: int) -> LoanRefinanceAnalysis:
        """Analyze refinancing options for a loan."""
        loan = self._get_loan(loan_id)
        if not loan or loan['user_id'] != user_id:
            raise ValueError("Loan not found or unauthorized")

        # Get current loan details
        current_loan = {
            'remaining_balance': loan['current_balance'],
            'interest_rate': loan['interest_rate'],
            'monthly_payment': loan['monthly_payment'],
            'remaining_months': loan['payments_remaining'],
            'total_remaining_interest': self._calculate_remaining_interest(loan)
        }

        # Generate refinance options
        refinance_options = self._generate_refinance_options(loan)

        # Calculate savings
        best_option = min(refinance_options, key=lambda x: x['total_cost'])
        current_total = current_loan['remaining_balance'] + current_loan['total_remaining_interest']
        total_savings = current_total - best_option['total_cost']
        monthly_savings = current_loan['monthly_payment'] - best_option['monthly_payment']

        # Calculate break-even
        closing_costs = best_option.get('closing_costs', 0)
        break_even_months = int(closing_costs / monthly_savings) if monthly_savings > 0 else 999

        return LoanRefinanceAnalysis(
            current_loan=current_loan,
            refinance_options=refinance_options,
            break_even_months=break_even_months,
            total_savings=total_savings,
            monthly_savings=monthly_savings,
            recommendation="Refinancing recommended" if total_savings > closing_costs else "Keep current loan",
            factors_considered=[
                "Interest rate comparison",
                "Remaining loan term",
                "Closing costs",
                "Monthly payment change",
                "Total interest savings"
            ]
        )

    def get_loan_summary_stats(self, user_id: int) -> LoanSummaryStats:
        """Get summary statistics for all user loans."""
        user_loans = [
            loan for loan in self.data_manager.loans
            if loan['user_id'] == user_id and loan.get('status') == 'active'
        ]

        if not user_loans:
            return LoanSummaryStats(
                total_loans=0,
                total_original_amount=0,
                total_current_balance=0,
                total_monthly_payments=0,
                average_interest_rate=0,
                total_interest_paid=0,
                loans_by_type={},
                next_payment_total=0,
                next_payment_date=None
            )

        loans_by_type = {}
        for loan in user_loans:
            loan_type = loan['loan_type']
            loans_by_type[loan_type] = loans_by_type.get(loan_type, 0) + 1

        next_payment_date = min(
            (loan['next_payment_date'] for loan in user_loans if loan['next_payment_date']),
            default=None
        )

        return LoanSummaryStats(
            total_loans=len(user_loans),
            total_original_amount=sum(loan['original_amount'] for loan in user_loans),
            total_current_balance=sum(loan['current_balance'] for loan in user_loans),
            total_monthly_payments=sum(loan['monthly_payment'] for loan in user_loans),
            average_interest_rate=sum(loan['interest_rate'] for loan in user_loans) / len(user_loans),
            total_interest_paid=sum(loan['total_interest_paid'] for loan in user_loans),
            loans_by_type=loans_by_type,
            next_payment_total=sum(loan['next_payment_amount'] for loan in user_loans),
            next_payment_date=next_payment_date
        )

    # Helper methods
    def _get_application(self, application_id: int) -> dict[str, Any] | None:
        """Get loan application by ID."""
        for app in self.data_manager.loan_applications:
            if app['id'] == application_id:
                return app
        return None

    def _get_offer(self, offer_id: int) -> dict[str, Any] | None:
        """Get loan offer by ID."""
        for offer in self.data_manager.loan_offers:
            if offer['id'] == offer_id:
                return offer
        return None

    def _get_loan(self, loan_id: int) -> dict[str, Any] | None:
        """Get loan by ID."""
        for loan in self.data_manager.loans:
            if loan['id'] == loan_id:
                return loan
        return None

    def _get_scheduled_payment(self, loan_id: int, payment_number: int) -> dict[str, Any] | None:
        """Get scheduled payment info."""
        for sched in self.data_manager.loan_payment_schedules:
            if sched['loan_id'] == loan_id and sched['payment_number'] == payment_number:
                return sched
        return None

    def _get_user_credit_score(self, user_id: int) -> int:
        """Get user's credit score (mock implementation)."""
        # In real implementation, this would fetch from credit bureau
        return 650 + (user_id % 150)  # Mock score between 650-800

    def _calculate_dti_ratio(self, user_id: int, annual_income: float, monthly_expenses: float) -> float:
        """Calculate debt-to-income ratio."""
        # Get existing loan payments
        existing_loans = [
            loan for loan in self.data_manager.loans
            if loan['user_id'] == user_id and loan['status'] == LoanStatus.ACTIVE
        ]
        total_debt_payments = sum(loan['monthly_payment'] for loan in existing_loans)

        monthly_income = annual_income / 12
        total_monthly_debt = monthly_expenses + total_debt_payments

        return (total_monthly_debt / monthly_income) * 100 if monthly_income > 0 else 0

    def _calculate_monthly_payment(self, principal: float, annual_rate: float, term_months: int) -> float:
        """Calculate monthly payment using amortization formula."""
        if annual_rate == 0:
            return principal / term_months

        monthly_rate = annual_rate / 100 / 12
        return principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)

    def _calculate_next_payment_date(self, from_date: date | None = None) -> date:
        """Calculate next payment date (monthly)."""
        base_date = from_date or date.today()
        return self._add_months(base_date, 1)

    def _calculate_maturity_date(self, term_months: int) -> date:
        """Calculate loan maturity date."""
        return self._add_months(date.today(), term_months)

    def _add_months(self, start_date: date, months: int) -> date:
        """Add months to a date."""
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(start_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                   31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)

    def _calculate_payoff_interest(self, loan: dict[str, Any], payoff_date: date) -> float:
        """Calculate interest for payoff."""
        days_since_last_payment = (payoff_date - (loan['last_payment_date'] or loan['originated_date'])).days
        daily_rate = loan['interest_rate'] / 100 / 365
        return loan['current_balance'] * daily_rate * days_since_last_payment

    def _calculate_remaining_interest(self, loan: dict[str, Any]) -> float:
        """Calculate total remaining interest."""
        total_payments = loan['monthly_payment'] * loan['payments_remaining']
        return total_payments - loan['current_balance']

    def _create_loan_account(self, user_id: int, offer: dict[str, Any]) -> int:
        """Create an account for the loan."""
        account = {
            'id': len(self.data_manager.accounts) + 1,
            'user_id': user_id,
            'account_type': 'LOAN',
            'account_name': f"{offer['lender_name']} Loan",
            'account_number': f"LN{uuid.uuid4().hex[:8].upper()}",
            'currency': 'USD',
            'balance': -offer['approved_amount'],  # Negative for liability
            'available_balance': 0,
            'status': 'ACTIVE',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        self.data_manager.accounts.append(account)
        return account['id']

    def _generate_loan_offers(self, application: dict[str, Any]) -> list[LoanOfferResponse]:
        """Generate loan offers based on application."""
        offers = []
        credit_score = application['credit_score_at_application']

        # Define lender profiles
        lenders = [
            {'name': 'QuickCash Bank', 'base_rate': 6.5, 'fee': 1.5},
            {'name': 'Premier Lending', 'base_rate': 5.8, 'fee': 2.0},
            {'name': 'Community Credit Union', 'base_rate': 5.5, 'fee': 1.0}
        ]

        for lender in lenders:
            # Calculate offer based on credit score
            if credit_score < 650 and lender['name'] == 'Premier Lending':
                continue  # This lender doesn't work with lower scores

            rate_adjustment = max(0, (750 - credit_score) * 0.02)
            interest_rate = lender['base_rate'] + rate_adjustment

            # Adjust approved amount based on DTI
            dti = application['debt_to_income_ratio']
            approved_amount = application['requested_amount']
            if dti > 40:
                approved_amount *= 0.8
            elif dti > 35:
                approved_amount *= 0.9

            # Calculate loan terms
            monthly_payment = self._calculate_monthly_payment(
                approved_amount,
                interest_rate,
                application['term_months']
            )

            total_payments = monthly_payment * application['term_months']
            total_interest = total_payments - approved_amount
            origination_fee = approved_amount * (lender['fee'] / 100)

            # Calculate APR (simplified)
            apr = interest_rate + (origination_fee / approved_amount / application['term_months'] * 12 * 100)

            offer_data = {
                'id': len(self.data_manager.loan_offers) + 1,
                'application_id': application['id'],
                'lender_name': lender['name'],
                'approved_amount': round(approved_amount, 2),
                'interest_rate': round(interest_rate, 3),
                'interest_type': InterestType.FIXED,
                'term_months': application['term_months'],
                'monthly_payment': round(monthly_payment, 2),
                'total_interest': round(total_interest, 2),
                'total_cost': round(total_payments + origination_fee, 2),
                'origination_fee': round(origination_fee, 2),
                'apr': round(apr, 3),
                'special_conditions': [],
                'expires_at': datetime.utcnow() + timedelta(days=30),
                'created_at': datetime.utcnow()
            }

            self.data_manager.loan_offers.append(offer_data)
            offers.append(LoanOfferResponse(**offer_data))

        return offers

    def _generate_payment_schedule(self, loan: dict[str, Any]) -> None:
        """Generate payment schedule for a loan."""
        remaining_balance = loan['original_amount']
        monthly_rate = loan['interest_rate'] / 100 / 12
        payment_date = loan['next_payment_date']

        for i in range(1, loan['term_months'] + 1):
            interest = remaining_balance * monthly_rate
            principal = loan['monthly_payment'] - interest
            remaining_balance -= principal

            schedule_entry = {
                'loan_id': loan['id'],
                'payment_number': i,
                'payment_date': payment_date,
                'payment_amount': loan['monthly_payment'],
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'remaining_balance': round(max(0, remaining_balance), 2),
                'cumulative_interest': round(interest * i, 2),
                'cumulative_principal': round(principal * i, 2)
            }

            self.data_manager.loan_payment_schedules.append(schedule_entry)
            payment_date = self._add_months(payment_date, 1)

    def _generate_refinance_options(self, loan: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate refinance options for a loan."""
        options = []
        current_balance = loan['current_balance']

        # Different refinance scenarios
        scenarios = [
            {'term': 15 * 12, 'rate_reduction': 0.5},
            {'term': 20 * 12, 'rate_reduction': 0.3},
            {'term': 30 * 12, 'rate_reduction': 0.1}
        ]

        for scenario in scenarios:
            new_rate = max(3.0, loan['interest_rate'] - scenario['rate_reduction'])
            new_payment = self._calculate_monthly_payment(
                current_balance,
                new_rate,
                scenario['term']
            )

            total_payments = new_payment * scenario['term']
            total_interest = total_payments - current_balance
            closing_costs = current_balance * 0.02  # 2% closing costs

            options.append({
                'lender': 'Refinance Partners',
                'term_months': scenario['term'],
                'interest_rate': round(new_rate, 3),
                'monthly_payment': round(new_payment, 2),
                'total_interest': round(total_interest, 2),
                'total_cost': round(total_payments + closing_costs, 2),
                'closing_costs': round(closing_costs, 2),
                'savings_vs_current': round(
                    (loan['monthly_payment'] * loan['payments_remaining']) - (total_payments + closing_costs), 2
                )
            })

        return options
