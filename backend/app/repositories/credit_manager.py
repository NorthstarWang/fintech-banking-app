"""
Credit manager for generating comprehensive mock credit data.
"""
import random
from datetime import datetime, timedelta

from ..models import (
    CreditAlertSeverity,
    CreditAlertType,
    CreditBuilderType,
    CreditDisputeStatus,
    CreditDisputeType,
    CreditFactorType,
    CreditScoreProvider,
    CreditScoreRange,
)
from ..utils.money import format_money


class CreditManager:
    """Manager for credit-related data generation and management."""

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def generate_credit_data(self, user_id: int, seed: int = 42):
        """Generate comprehensive credit data for a user."""
        random.seed(seed + user_id)

        # Generate credit scores with history
        self._generate_credit_scores(user_id)

        # Generate credit alerts
        self._generate_credit_alerts(user_id)

        # Generate credit disputes
        self._generate_credit_disputes(user_id)

        # Generate credit builder accounts
        self._generate_credit_builder_accounts(user_id)

        # Generate credit simulations
        self._generate_credit_simulations(user_id)

    def _generate_credit_scores(self, user_id: int):
        """Generate credit score history for a user."""
        # Base score varies by user
        base_score = 600 + (user_id * 17) % 150

        # Generate scores for the last 24 months
        for months_ago in range(24):
            score_date = datetime.utcnow() - timedelta(days=months_ago * 30)

            # Add variation over time
            variation = random.randint(-20, 25)
            score = max(300, min(850, base_score + variation - (months_ago * 2)))

            # Create score for each provider (alternate months)
            if months_ago % 3 == 0:
                provider = CreditScoreProvider.EQUIFAX
            elif months_ago % 3 == 1:
                provider = CreditScoreProvider.EXPERIAN
            else:
                provider = CreditScoreProvider.TRANSUNION

            score_range = self._calculate_score_range(score)
            factors = self._generate_score_factors(score)

            credit_score = {
                'id': len(self.data_manager.credit_scores) + 1,
                'user_id': user_id,
                'score': score,
                'provider': provider.value,
                'score_range': score_range.value,
                'factors': factors,
                'last_updated': score_date,
                'next_update': score_date + timedelta(days=30),
                'created_at': score_date
            }

            self.data_manager.credit_scores.append(credit_score)

            # Update base score for next iteration
            base_score = score

    def _calculate_score_range(self, score: int) -> CreditScoreRange:
        """Calculate credit score range."""
        if score >= 800:
            return CreditScoreRange.EXCELLENT
        if score >= 740:
            return CreditScoreRange.VERY_GOOD
        if score >= 670:
            return CreditScoreRange.GOOD
        if score >= 580:
            return CreditScoreRange.FAIR
        return CreditScoreRange.POOR

    def _generate_score_factors(self, score: int) -> list[dict]:
        """Generate credit score factors."""
        factors = []

        # Payment history (35%)
        payment_score = min(100, (score - 300) * 0.35 / 5.5)
        factors.append({
            "factor_type": CreditFactorType.PAYMENT_HISTORY.value,
            "score": round(payment_score),
            "impact": "high",
            "description": "Payment history affects 35% of your score"
        })

        # Credit utilization (30%)
        utilization_score = min(100, (score - 300) * 0.30 / 5.5)
        factors.append({
            "factor_type": CreditFactorType.CREDIT_UTILIZATION.value,
            "score": round(utilization_score),
            "impact": "high",
            "description": "Credit utilization affects 30% of your score"
        })

        # Credit age (15%)
        age_score = min(100, (score - 300) * 0.15 / 5.5)
        factors.append({
            "factor_type": CreditFactorType.CREDIT_AGE.value,
            "score": round(age_score),
            "impact": "medium",
            "description": "Length of credit history affects 15% of your score"
        })

        # Credit mix (10%)
        mix_score = min(100, (score - 300) * 0.10 / 5.5)
        factors.append({
            "factor_type": CreditFactorType.CREDIT_MIX.value,
            "score": round(mix_score),
            "impact": "low",
            "description": "Credit mix affects 10% of your score"
        })

        # New credit (10%)
        new_credit_score = min(100, (score - 300) * 0.10 / 5.5)
        factors.append({
            "factor_type": CreditFactorType.NEW_CREDIT.value,
            "score": round(new_credit_score),
            "impact": "low",
            "description": "New credit inquiries affect 10% of your score"
        })

        return factors

    def _generate_credit_alerts(self, user_id: int):
        """Generate credit alerts for a user."""
        alert_templates = [
            {
                'type': CreditAlertType.SCORE_CHANGE,
                'severity': CreditAlertSeverity.INFO,
                'title': 'Credit Score Increased',
                'description': 'Your Equifax score increased by 15 points to 725',
                'action_required': False
            },
            {
                'type': CreditAlertType.NEW_INQUIRY,
                'severity': CreditAlertSeverity.WARNING,
                'title': 'New Credit Inquiry Detected',
                'description': 'Capital One performed a hard inquiry on your credit report',
                'action_required': True,
                'action_url': '/credit/report'
            },
            {
                'type': CreditAlertType.PAYMENT_REPORTED,
                'severity': CreditAlertSeverity.INFO,
                'title': 'On-Time Payment Reported',
                'description': 'Your Chase credit card payment was reported as on-time',
                'action_required': False
            },
            {
                'type': CreditAlertType.FRAUD_ALERT,
                'severity': CreditAlertSeverity.CRITICAL,
                'title': 'Potential Fraud Detected',
                'description': 'Unusual activity detected on your credit report',
                'action_required': True,
                'action_url': '/credit/disputes'
            },
            {
                'type': CreditAlertType.NEW_ACCOUNT,
                'severity': CreditAlertSeverity.INFO,
                'title': 'New Account Added',
                'description': 'A new credit card account was added to your report',
                'action_required': False
            }
        ]

        # Generate 3-8 alerts per user
        num_alerts = random.randint(3, 8)
        selected_alerts = random.sample(alert_templates, min(num_alerts, len(alert_templates)))

        for i, alert_template in enumerate(selected_alerts):
            days_ago = random.randint(0, 90)
            alert_date = datetime.utcnow() - timedelta(days=days_ago)

            alert = {
                'id': len(self.data_manager.credit_alerts) + 1,
                'user_id': user_id,
                'alert_type': alert_template['type'] if isinstance(alert_template['type'], str) else alert_template['type'].value,
                'severity': alert_template['severity'] if isinstance(alert_template['severity'], str) else alert_template['severity'].value,
                'title': alert_template['title'],
                'description': alert_template['description'],
                'is_read': random.random() < 0.7,  # 70% read
                'is_dismissed': random.random() < 0.3,  # 30% dismissed
                'action_required': alert_template.get('action_required', False),
                'action_url': alert_template.get('action_url'),
                'metadata': {
                    'source': random.choice(['monitoring', 'bureau_update', 'user_action']),
                    'alert_id': f'ALT{alert_date.strftime("%Y%m%d")}{i:03d}'
                },
                'alert_date': alert_date,
                'created_at': alert_date
            }

            self.data_manager.credit_alerts.append(alert)

    def _generate_credit_disputes(self, user_id: int):
        """Generate credit disputes for a user."""
        # 40% chance of having disputes
        if random.random() > 0.4:
            return

        dispute_templates = [
            {
                'type': CreditDisputeType.INCORRECT_INFO,
                'account': 'ABC Collections',
                'reason': 'This account was paid in full',
                'details': 'I paid this account on March 15, 2023. I have receipts showing full payment.'
            },
            {
                'type': CreditDisputeType.NOT_MINE,
                'account': 'XYZ Credit Card',
                'reason': 'I never opened this account',
                'details': 'This account does not belong to me. I have never had a relationship with XYZ Bank.'
            },
            {
                'type': CreditDisputeType.FRAUD,
                'account': 'Quick Loans Inc',
                'reason': 'Fraudulent account opened in my name',
                'details': 'This account was opened fraudulently. I have filed a police report.'
            }
        ]

        num_disputes = random.randint(1, 2)
        selected_disputes = random.sample(dispute_templates, num_disputes)

        for dispute_template in selected_disputes:
            # Random filing date in last 6 months
            days_ago = random.randint(30, 180)
            filed_date = datetime.utcnow() - timedelta(days=days_ago)

            # Determine status based on age
            if days_ago > 120:
                status = CreditDisputeStatus.RESOLVED
                outcome = random.choice(['removed', 'corrected', 'verified'])
                resolution_date = filed_date + timedelta(days=random.randint(30, 60))
            elif days_ago > 60:
                status = CreditDisputeStatus.IN_PROGRESS
                outcome = None
                resolution_date = None
            else:
                status = CreditDisputeStatus.PENDING
                outcome = None
                resolution_date = None

            dispute = {
                'id': len(self.data_manager.credit_disputes) + 1,
                'user_id': user_id,
                'dispute_type': dispute_template['type'] if isinstance(dispute_template['type'], str) else dispute_template['type'].value,
                'status': status if isinstance(status, str) else status.value,
                'bureau': random.choice(['equifax', 'experian', 'transunion']),
                'account_name': dispute_template['account'],
                'dispute_reason': dispute_template['reason'],
                'dispute_details': dispute_template['details'],
                'supporting_documents': [f'document_{i}.pdf' for i in range(random.randint(1, 3))],
                'bureau_response': 'We are investigating your dispute' if status != CreditDisputeStatus.PENDING else None,
                'outcome': outcome,
                'filed_date': filed_date,
                'last_updated': filed_date + timedelta(days=random.randint(1, 30)),
                'resolution_date': resolution_date,
                'created_at': filed_date
            }

            self.data_manager.credit_disputes.append(dispute)

    def _generate_credit_builder_accounts(self, user_id: int):
        """Generate credit builder accounts for a user."""
        # 60% chance of having credit builder account
        if random.random() > 0.6:
            return

        account_types = [
            {
                'type': CreditBuilderType.SECURED_CARD,
                'secured_amount': 500.0,
                'credit_limit': 500.0,
                'monthly_fee': 0.0
            },
            {
                'type': CreditBuilderType.CREDIT_BUILDER_LOAN,
                'secured_amount': 1000.0,
                'credit_limit': 1000.0,
                'monthly_fee': 5.0
            }
        ]

        # Most users have 1, some have 2
        num_accounts = 1 if random.random() < 0.8 else 2
        selected_accounts = random.sample(account_types, num_accounts)

        for account_template in selected_accounts:
            # Account age in months
            account_age_months = random.randint(3, 24)
            opened_date = datetime.utcnow() - timedelta(days=account_age_months * 30)

            # Generate payment history
            payment_history = []
            current_balance = account_template['secured_amount']

            for month in range(min(account_age_months, 12)):
                payment_date = opened_date + timedelta(days=(month + 1) * 30)
                payment_amount = account_template['secured_amount'] / 12  # 12-month term
                on_time = random.random() < 0.9  # 90% on-time

                payment_history.append({
                    'date': payment_date.isoformat(),
                    'amount': round(payment_amount, 2),
                    'on_time': on_time
                })

                if on_time:
                    current_balance -= payment_amount

            # Check graduation eligibility
            graduation_eligible = False
            if len(payment_history) >= 12:
                on_time_count = sum(1 for p in payment_history[-12:] if p['on_time'])
                graduation_eligible = on_time_count >= 11

            account = {
                'id': len(self.data_manager.credit_builder_accounts) + 1,
                'user_id': user_id,
                'account_type': account_template['type'] if isinstance(account_template['type'], str) else account_template['type'].value,
                'status': 'graduated' if graduation_eligible and random.random() < 0.5 else 'active',
                'secured_amount': format_money(account_template['secured_amount']),
                'credit_limit': format_money(account_template['credit_limit']),
                'current_balance': format_money(max(0, current_balance)),
                'payment_history': payment_history,
                'graduation_eligible': graduation_eligible,
                'graduation_date': datetime.utcnow() if graduation_eligible else None,
                'reports_to_bureaus': ['equifax', 'experian', 'transunion'],
                'auto_pay_enabled': random.random() < 0.7,
                'monthly_fee': format_money(account_template['monthly_fee']),
                'opened_date': opened_date,
                'last_payment_date': payment_history[-1]['date'] if payment_history else None,
                'created_at': opened_date
            }

            self.data_manager.credit_builder_accounts.append(account)

    def _generate_credit_simulations(self, user_id: int):
        """Generate credit simulation history for a user."""
        simulation_types = [
            {
                'action': 'pay_off_debt',
                'details': {'amount': 2000, 'total_credit_limit': 10000},
                'score_change': 25,
                'time_months': 1
            },
            {
                'action': 'open_new_card',
                'details': {'credit_limit': 5000},
                'score_change': 2,
                'time_months': 3
            },
            {
                'action': 'close_card',
                'details': {'card_age_years': 5, 'credit_limit': 3000},
                'score_change': -20,
                'time_months': 1
            }
        ]

        # Generate 2-5 simulations
        num_simulations = random.randint(2, 5)

        for _i in range(num_simulations):
            sim_template = random.choice(simulation_types)
            days_ago = random.randint(1, 90)
            simulation_date = datetime.utcnow() - timedelta(days=days_ago)

            # Get a base score
            base_score = 650 + (user_id * 7) % 100

            simulation = {
                'id': len(self.data_manager.credit_simulations) + 1,
                'user_id': user_id,
                'current_score': base_score,
                'projected_score': base_score + sim_template['score_change'],
                'score_change': sim_template['score_change'],
                'time_to_change_months': sim_template['time_months'],
                'simulation_type': sim_template['action'],
                'simulation_details': sim_template['details'],
                'impact_factors': self._generate_impact_factors(sim_template['action']),
                'recommendations': self._generate_recommendations(sim_template['action']),
                'simulation_date': simulation_date,
                'created_at': simulation_date
            }

            self.data_manager.credit_simulations.append(simulation)

    def _generate_impact_factors(self, action_type: str) -> list[dict]:
        """Generate impact factors for a simulation."""
        if action_type == 'pay_off_debt':
            return [
                {
                    'factor': 'Credit Utilization',
                    'impact': '+25 points',
                    'description': 'Lower utilization improves score'
                }
            ]
        if action_type == 'open_new_card':
            return [
                {
                    'factor': 'Hard Inquiry',
                    'impact': '-5 points',
                    'description': 'Temporary impact from credit check'
                },
                {
                    'factor': 'Credit Mix',
                    'impact': '+7 points',
                    'description': 'Improved credit mix'
                }
            ]
        # close_card
        return [
            {
                'factor': 'Credit Utilization',
                'impact': '-15 points',
                'description': 'Higher utilization ratio'
            },
            {
                'factor': 'Credit History',
                'impact': '-5 points',
                'description': 'Lost account history'
            }
        ]

    def _generate_recommendations(self, action_type: str) -> list[str]:
        """Generate recommendations for a simulation."""
        if action_type == 'pay_off_debt':
            return [
                'Continue making on-time payments',
                'Keep credit cards open to maintain history',
                'Monitor utilization monthly'
            ]
        if action_type == 'open_new_card':
            return [
                'Wait 6 months before next application',
                'Keep utilization below 30%',
                'Set up automatic payments'
            ]
        # close_card
        return [
            'Consider keeping the card open',
            'Pay down other balances first',
            'Request credit limit increases on remaining cards'
        ]
