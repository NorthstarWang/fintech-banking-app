"""
Loan calculation utilities for amortization, payments, and financial analysis.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math

class LoanCalculator:
    """Utilities for loan calculations and financial analysis."""
    
    @staticmethod
    def calculate_monthly_payment(
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> float:
        """
        Calculate monthly payment using standard amortization formula.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate as percentage (e.g., 5.5 for 5.5%)
            term_months: Loan term in months
            
        Returns:
            Monthly payment amount
        """
        if annual_rate == 0:
            return principal / term_months
        
        monthly_rate = annual_rate / 100 / 12
        payment = principal * (monthly_rate * (1 + monthly_rate)**term_months) / \
                 ((1 + monthly_rate)**term_months - 1)
        
        return round(payment, 2)
    
    @staticmethod
    def generate_amortization_schedule(
        principal: float,
        annual_rate: float,
        term_months: int,
        start_date: Optional[date] = None,
        extra_payment: float = 0,
        extra_payment_frequency: str = "monthly"
    ) -> List[Dict[str, Any]]:
        """
        Generate complete amortization schedule with payment breakdown.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate as percentage
            term_months: Loan term in months
            start_date: First payment date (defaults to next month)
            extra_payment: Additional payment amount
            extra_payment_frequency: How often to apply extra payment
            
        Returns:
            List of payment schedule entries
        """
        if start_date is None:
            start_date = date.today().replace(day=1) + timedelta(days=32)
            start_date = start_date.replace(day=1)
        
        monthly_payment = LoanCalculator.calculate_monthly_payment(
            principal, annual_rate, term_months
        )
        
        schedule = []
        remaining_balance = principal
        monthly_rate = annual_rate / 100 / 12
        payment_date = start_date
        cumulative_interest = 0
        cumulative_principal = 0
        
        for payment_num in range(1, term_months + 1):
            # Calculate interest for this period
            interest_payment = remaining_balance * monthly_rate
            
            # Calculate principal payment
            principal_payment = monthly_payment - interest_payment
            
            # Apply extra payment if applicable
            extra = 0
            if extra_payment > 0:
                if extra_payment_frequency == "monthly":
                    extra = extra_payment
                elif extra_payment_frequency == "quarterly" and payment_num % 3 == 0:
                    extra = extra_payment
                elif extra_payment_frequency == "annually" and payment_num % 12 == 0:
                    extra = extra_payment
            
            principal_payment += extra
            
            # Don't overpay the loan
            if principal_payment > remaining_balance:
                principal_payment = remaining_balance
            
            # Update balances
            remaining_balance -= principal_payment
            cumulative_interest += interest_payment
            cumulative_principal += principal_payment
            
            # Create schedule entry
            entry = {
                "payment_number": payment_num,
                "payment_date": payment_date,
                "payment_amount": round(monthly_payment + extra, 2),
                "principal": round(principal_payment, 2),
                "interest": round(interest_payment, 2),
                "extra_payment": round(extra, 2),
                "remaining_balance": round(max(0, remaining_balance), 2),
                "cumulative_interest": round(cumulative_interest, 2),
                "cumulative_principal": round(cumulative_principal, 2)
            }
            
            schedule.append(entry)
            
            # If loan is paid off early, stop
            if remaining_balance <= 0:
                break
            
            # Calculate next payment date
            payment_date = LoanCalculator._add_months(payment_date, 1)
        
        return schedule
    
    @staticmethod
    def calculate_payoff_amount(
        current_balance: float,
        annual_rate: float,
        last_payment_date: date,
        payoff_date: date
    ) -> Dict[str, float]:
        """
        Calculate payoff amount including per-diem interest.
        
        Returns:
            Dict with principal, interest, and total payoff amounts
        """
        days_since_payment = (payoff_date - last_payment_date).days
        daily_rate = annual_rate / 100 / 365
        interest_accrued = current_balance * daily_rate * days_since_payment
        
        return {
            "principal": round(current_balance, 2),
            "interest": round(interest_accrued, 2),
            "total": round(current_balance + interest_accrued, 2),
            "days_of_interest": days_since_payment
        }
    
    @staticmethod
    def analyze_extra_payments(
        principal: float,
        annual_rate: float,
        term_months: int,
        extra_payment: float,
        extra_payment_frequency: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Analyze the impact of making extra payments.
        
        Returns:
            Analysis including time saved, interest saved, etc.
        """
        # Calculate baseline without extra payments
        baseline_schedule = LoanCalculator.generate_amortization_schedule(
            principal, annual_rate, term_months
        )
        baseline_interest = sum(p["interest"] for p in baseline_schedule)
        baseline_months = len(baseline_schedule)
        
        # Calculate with extra payments
        extra_schedule = LoanCalculator.generate_amortization_schedule(
            principal, annual_rate, term_months, 
            extra_payment=extra_payment,
            extra_payment_frequency=extra_payment_frequency
        )
        extra_interest = sum(p["interest"] for p in extra_schedule)
        extra_months = len(extra_schedule)
        
        # Calculate savings
        months_saved = baseline_months - extra_months
        interest_saved = baseline_interest - extra_interest
        
        # Calculate total extra paid
        total_extra = sum(p["extra_payment"] for p in extra_schedule)
        
        return {
            "baseline_months": baseline_months,
            "accelerated_months": extra_months,
            "months_saved": months_saved,
            "years_saved": round(months_saved / 12, 1),
            "baseline_interest": round(baseline_interest, 2),
            "accelerated_interest": round(extra_interest, 2),
            "interest_saved": round(interest_saved, 2),
            "total_extra_payments": round(total_extra, 2),
            "roi_on_extra_payments": round((interest_saved / total_extra * 100) if total_extra > 0 else 0, 1)
        }
    
    @staticmethod
    def calculate_apr(
        loan_amount: float,
        interest_rate: float,
        term_months: int,
        fees: Dict[str, float]
    ) -> float:
        """
        Calculate Annual Percentage Rate (APR) including fees.
        
        Args:
            loan_amount: Principal amount
            interest_rate: Nominal interest rate
            term_months: Loan term
            fees: Dict of fee_name -> amount
            
        Returns:
            APR as percentage
        """
        total_fees = sum(fees.values())
        
        # If no fees, APR equals interest rate
        if total_fees == 0:
            return interest_rate
        
        # Calculate monthly payment on full amount
        monthly_payment = LoanCalculator.calculate_monthly_payment(
            loan_amount, interest_rate, term_months
        )
        
        # Use Newton's method to find APR
        # APR is the rate where PV of payments equals loan minus fees
        net_loan = loan_amount - total_fees
        
        # Initial guess
        apr_guess = interest_rate
        
        for _ in range(100):  # Max iterations
            monthly_apr = apr_guess / 100 / 12
            
            if monthly_apr == 0:
                pv = monthly_payment * term_months
            else:
                pv = monthly_payment * ((1 - (1 + monthly_apr)**(-term_months)) / monthly_apr)
            
            # Calculate derivative
            if monthly_apr == 0:
                dpv = 0
            else:
                dpv = monthly_payment * (
                    -((1 - (1 + monthly_apr)**(-term_months)) / (monthly_apr**2)) +
                    (term_months * (1 + monthly_apr)**(-term_months - 1) / monthly_apr)
                )
            
            # Newton's method update
            error = pv - net_loan
            if abs(error) < 0.01:  # Close enough
                break
            
            if dpv != 0:
                apr_guess = apr_guess - (error / dpv) * 12 * 100
            else:
                break
        
        return round(apr_guess, 3)
    
    @staticmethod
    def compare_loans(loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compare multiple loan offers.
        
        Args:
            loans: List of loan dicts with amount, rate, term_months, fees
            
        Returns:
            Comparison including monthly payment, total cost, etc.
        """
        comparisons = []
        
        for loan in loans:
            amount = loan["amount"]
            rate = loan["rate"]
            term = loan["term_months"]
            fees = loan.get("fees", {})
            
            monthly_payment = LoanCalculator.calculate_monthly_payment(
                amount, rate, term
            )
            
            total_payments = monthly_payment * term
            total_interest = total_payments - amount
            total_fees = sum(fees.values())
            total_cost = total_payments + total_fees
            
            apr = LoanCalculator.calculate_apr(amount, rate, term, fees)
            
            comparisons.append({
                "loan_name": loan.get("name", "Loan"),
                "amount": amount,
                "rate": rate,
                "term_months": term,
                "monthly_payment": round(monthly_payment, 2),
                "total_payments": round(total_payments, 2),
                "total_interest": round(total_interest, 2),
                "total_fees": round(total_fees, 2),
                "total_cost": round(total_cost, 2),
                "apr": apr,
                "cost_per_thousand": round((total_cost / amount) * 1000, 2)
            })
        
        # Sort by total cost
        comparisons.sort(key=lambda x: x["total_cost"])
        
        # Add savings compared to most expensive
        if len(comparisons) > 1:
            max_cost = max(c["total_cost"] for c in comparisons)
            for comp in comparisons:
                comp["savings_vs_highest"] = round(max_cost - comp["total_cost"], 2)
        
        return comparisons
    
    @staticmethod
    def calculate_refinance_breakeven(
        current_loan: Dict[str, Any],
        new_loan: Dict[str, Any],
        closing_costs: float
    ) -> Dict[str, Any]:
        """
        Calculate break-even point for refinancing.
        
        Args:
            current_loan: Dict with balance, rate, remaining_months
            new_loan: Dict with rate, term_months
            closing_costs: Total refinancing costs
            
        Returns:
            Break-even analysis
        """
        current_balance = current_loan["balance"]
        current_rate = current_loan["rate"]
        current_remaining = current_loan["remaining_months"]
        
        new_rate = new_loan["rate"]
        new_term = new_loan["term_months"]
        
        # Calculate current monthly payment
        current_payment = LoanCalculator.calculate_monthly_payment(
            current_balance, current_rate, current_remaining
        )
        
        # Calculate new monthly payment
        new_payment = LoanCalculator.calculate_monthly_payment(
            current_balance, new_rate, new_term
        )
        
        # Monthly savings
        monthly_savings = current_payment - new_payment
        
        # Break-even in months
        if monthly_savings > 0:
            breakeven_months = math.ceil(closing_costs / monthly_savings)
        else:
            breakeven_months = float('inf')
        
        # Calculate total interest for both scenarios
        current_total_interest = (current_payment * current_remaining) - current_balance
        new_total_interest = (new_payment * new_term) - current_balance
        
        # Lifetime savings
        lifetime_savings = current_total_interest - new_total_interest - closing_costs
        
        return {
            "current_payment": round(current_payment, 2),
            "new_payment": round(new_payment, 2),
            "monthly_savings": round(monthly_savings, 2),
            "closing_costs": round(closing_costs, 2),
            "breakeven_months": breakeven_months if breakeven_months != float('inf') else None,
            "breakeven_years": round(breakeven_months / 12, 1) if breakeven_months != float('inf') else None,
            "lifetime_savings": round(lifetime_savings, 2),
            "current_total_interest": round(current_total_interest, 2),
            "new_total_interest": round(new_total_interest, 2),
            "worth_refinancing": lifetime_savings > 0 and breakeven_months < new_term
        }
    
    @staticmethod
    def calculate_debt_to_income(
        monthly_income: float,
        monthly_debts: List[float],
        new_loan_payment: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate debt-to-income ratio.
        
        Returns:
            Current and projected DTI ratios
        """
        total_debts = sum(monthly_debts)
        current_dti = (total_debts / monthly_income * 100) if monthly_income > 0 else 0
        
        result = {
            "monthly_income": round(monthly_income, 2),
            "total_monthly_debts": round(total_debts, 2),
            "current_dti": round(current_dti, 2),
            "current_dti_status": LoanCalculator._get_dti_status(current_dti)
        }
        
        if new_loan_payment:
            projected_debts = total_debts + new_loan_payment
            projected_dti = (projected_debts / monthly_income * 100) if monthly_income > 0 else 0
            
            result.update({
                "new_loan_payment": round(new_loan_payment, 2),
                "projected_total_debts": round(projected_debts, 2),
                "projected_dti": round(projected_dti, 2),
                "projected_dti_status": LoanCalculator._get_dti_status(projected_dti),
                "dti_increase": round(projected_dti - current_dti, 2)
            })
        
        return result
    
    @staticmethod
    def calculate_loan_affordability(
        monthly_income: float,
        monthly_expenses: float,
        down_payment: float,
        interest_rate: float,
        term_months: int,
        max_dti: float = 43.0
    ) -> Dict[str, Any]:
        """
        Calculate maximum affordable loan amount.
        
        Returns:
            Maximum loan amount and related metrics
        """
        # Calculate maximum monthly payment based on DTI
        max_payment_dti = (monthly_income * max_dti / 100) - monthly_expenses
        
        # Also consider 28% front-end ratio for housing
        max_payment_frontend = monthly_income * 0.28
        
        # Use the lower of the two
        max_payment = min(max_payment_dti, max_payment_frontend)
        
        if max_payment <= 0:
            return {
                "affordable": False,
                "max_loan_amount": 0,
                "max_purchase_price": down_payment,
                "max_monthly_payment": 0,
                "reason": "Insufficient income after expenses"
            }
        
        # Calculate maximum loan amount
        if interest_rate == 0:
            max_loan = max_payment * term_months
        else:
            monthly_rate = interest_rate / 100 / 12
            max_loan = max_payment * ((1 - (1 + monthly_rate)**(-term_months)) / monthly_rate)
        
        max_purchase_price = max_loan + down_payment
        
        return {
            "affordable": True,
            "max_loan_amount": round(max_loan, 2),
            "max_purchase_price": round(max_purchase_price, 2),
            "max_monthly_payment": round(max_payment, 2),
            "down_payment": round(down_payment, 2),
            "down_payment_percentage": round((down_payment / max_purchase_price * 100), 1),
            "monthly_income": round(monthly_income, 2),
            "monthly_expenses": round(monthly_expenses, 2),
            "debt_to_income": round((max_payment + monthly_expenses) / monthly_income * 100, 1)
        }
    
    @staticmethod
    def _add_months(start_date: date, months: int) -> date:
        """Add months to a date, handling month-end correctly."""
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        
        # Handle month-end dates
        day = start_date.day
        while True:
            try:
                return date(year, month, day)
            except ValueError:
                day -= 1
    
    @staticmethod
    def _get_dti_status(dti: float) -> str:
        """Get DTI status description."""
        if dti <= 20:
            return "Excellent"
        elif dti <= 36:
            return "Good"
        elif dti <= 43:
            return "Acceptable"
        elif dti <= 50:
            return "Poor"
        else:
            return "Very Poor"