import random
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ..models import (
    Account,
    CreditAlert,
    CreditBuilderAccount,
    CreditDispute,
    CreditFactorType,
    CreditHistoryResponse,
    CreditReportResponse,
    CreditScore,
    CreditScoreProvider,
    CreditScoreRange,
    CreditScoreResponse,
    CreditSimulation,
    CreditSimulatorRequest,
    CreditSimulatorResponse,
    CreditTip,
    CreditTipsResponse,
    User,
)
from ..storage.memory_adapter import db
from ..utils.auth import get_current_user

router = APIRouter()

def calculate_credit_score_range(score: int) -> CreditScoreRange:
    """Determine credit score range category"""
    if score >= 800:
        return CreditScoreRange.EXCELLENT
    if score >= 740:
        return CreditScoreRange.VERY_GOOD
    if score >= 670:
        return CreditScoreRange.GOOD
    if score >= 580:
        return CreditScoreRange.FAIR
    return CreditScoreRange.POOR

def generate_mock_credit_score(user_id: int) -> int:
    """Generate a mock credit score based on user activity"""
    # In production, this would use real credit scoring algorithms
    base_score = 650
    # Add some variation based on user_id
    variation = (user_id * 7) % 150
    return min(850, base_score + variation)

def generate_score_factors(score: int) -> list[dict]:
    """Generate factors affecting credit score"""
    factors = []

    # Payment history (35% of score)
    payment_score = min(100, (score - 300) * 0.35 / 5.5)
    factors.append({
        "factor_type": CreditFactorType.PAYMENT_HISTORY.value,
        "score": round(payment_score),
        "impact": "high",
        "description": "On-time payment history"
    })

    # Credit utilization (30% of score)
    utilization_score = min(100, (score - 300) * 0.30 / 5.5)
    factors.append({
        "factor_type": CreditFactorType.CREDIT_UTILIZATION.value,
        "score": round(utilization_score),
        "impact": "high",
        "description": "Credit card utilization ratio"
    })

    # Credit age (15% of score)
    age_score = min(100, (score - 300) * 0.15 / 5.5)
    factors.append({
        "factor_type": CreditFactorType.CREDIT_AGE.value,
        "score": round(age_score),
        "impact": "medium",
        "description": "Length of credit history"
    })

    # Credit mix (10% of score)
    mix_score = min(100, (score - 300) * 0.10 / 5.5)
    factors.append({
        "factor_type": CreditFactorType.CREDIT_MIX.value,
        "score": round(mix_score),
        "impact": "low",
        "description": "Variety of credit accounts"
    })

    # New credit (10% of score)
    new_credit_score = min(100, (score - 300) * 0.10 / 5.5)
    factors.append({
        "factor_type": CreditFactorType.NEW_CREDIT.value,
        "score": round(new_credit_score),
        "impact": "low",
        "description": "Recent credit inquiries"
    })

    return factors

@router.get("/score", response_model=CreditScoreResponse)
async def get_credit_score(
    request: Request,
    provider: CreditScoreProvider = CreditScoreProvider.VANTAGE,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get current credit score"""

    # Check for existing score
    credit_score = db_session.query(CreditScore).filter(
        CreditScore.user_id == current_user['user_id'],
        CreditScore.provider == provider
    ).order_by(CreditScore.last_updated.desc()).first()

    # Generate new score if none exists or if it's outdated
    if not credit_score or (datetime.utcnow() - credit_score.last_updated).days > 30:
        score_value = generate_mock_credit_score(current_user['user_id'])
        score_range = calculate_credit_score_range(score_value)
        factors = generate_score_factors(score_value)

        credit_score = CreditScore(
            user_id=current_user['user_id'],
            score=score_value,
            provider=provider,
            score_range=score_range,
            payment_history_score=factors[0]["score"],
            credit_utilization_score=factors[1]["score"],
            credit_age_score=factors[2]["score"],
            credit_mix_score=factors[3]["score"],
            new_credit_score=factors[4]["score"],
            factors=factors,
            last_updated=datetime.utcnow(),
            next_update=datetime.utcnow() + timedelta(days=30)
        )

        db_session.add(credit_score)
        db_session.commit()
        db_session.refresh(credit_score)


    return CreditScoreResponse.from_orm(credit_score)

@router.get("/history", response_model=CreditHistoryResponse)
async def get_credit_history(
    months: int = 12,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get credit score history"""
    # Get historical scores
    since_date = datetime.utcnow() - timedelta(days=months * 30)

    scores = db_session.query(CreditScore).filter(
        CreditScore.user_id == current_user['user_id'],
        CreditScore.last_updated >= since_date
    ).order_by(CreditScore.last_updated).all()

    if not scores:
        # Generate some mock historical data
        current_score = generate_mock_credit_score(current_user['user_id'])
        scores_data = []

        for i in range(months):
            month_date = datetime.utcnow() - timedelta(days=i * 30)
            # Add some variation
            variation = random.randint(-10, 15)
            score = max(300, min(850, current_score - (i * 2) + variation))

            scores_data.append({
                "score": score,
                "date": month_date.isoformat(),
                "provider": CreditScoreProvider.VANTAGE.value
            })

        scores_data.reverse()
    else:
        scores_data = [
            {
                "score": s.score,
                "date": s.last_updated.isoformat(),
                "provider": s.provider.value
            }
            for s in scores
        ]

    # Calculate trend and changes
    if len(scores_data) >= 2:
        current = scores_data[-1]["score"]
        last_month = scores_data[-2]["score"] if len(scores_data) >= 2 else current
        last_year = scores_data[0]["score"] if len(scores_data) >= 12 else scores_data[0]["score"]

        change_last_month = current - last_month
        change_last_year = current - last_year

        if change_last_year > 10:
            trend = "improving"
        elif change_last_year < -10:
            trend = "declining"
        else:
            trend = "stable"
    else:
        current = scores_data[0]["score"] if scores_data else 650
        change_last_month = 0
        change_last_year = 0
        trend = "stable"

    average_score = sum(s["score"] for s in scores_data) / len(scores_data) if scores_data else current

    return CreditHistoryResponse(
        scores=scores_data,
        average_score=round(average_score),
        trend=trend,
        change_last_month=change_last_month,
        change_last_year=change_last_year
    )

@router.post("/simulator", response_model=CreditSimulatorResponse)
async def simulate_credit_action(
    request: Request,
    simulation: CreditSimulatorRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Simulate the impact of financial actions on credit score"""

    # Get current score
    if simulation.current_score:
        current_score = simulation.current_score
    else:
        score_response = await get_credit_score(request, CreditScoreProvider.VANTAGE, current_user, db_session)
        current_score = score_response.score

    # Simulate different actions
    projected_score = current_score
    time_to_change = 1
    impact_factors = []
    recommendations = []

    if simulation.action_type == "pay_off_debt":
        # Paying off debt improves credit utilization
        amount = simulation.action_details.get("amount", 1000)
        total_credit = simulation.action_details.get("total_credit_limit", 10000)

        utilization_improvement = (amount / total_credit) * 100
        score_increase = min(50, int(utilization_improvement * 1.5))
        projected_score = min(850, current_score + score_increase)
        time_to_change = 1

        impact_factors.append({
            "factor": "Credit Utilization",
            "impact": f"+{score_increase} points",
            "description": f"Lowering utilization by paying off ${amount}"
        })

        recommendations.append("Continue making on-time payments")
        recommendations.append("Keep credit cards open to maintain credit history")

    elif simulation.action_type == "open_new_card":
        # Opening new card has mixed effects
        credit_limit = simulation.action_details.get("credit_limit", 5000)

        # Negative: Hard inquiry
        inquiry_impact = -5
        # Positive: Increased total credit
        utilization_impact = 10
        # Negative: Lower average account age
        age_impact = -3

        net_impact = inquiry_impact + utilization_impact + age_impact
        projected_score = max(300, current_score + net_impact)
        time_to_change = 3

        impact_factors.extend([
            {
                "factor": "Hard Inquiry",
                "impact": f"{inquiry_impact} points",
                "description": "Temporary impact from credit check"
            },
            {
                "factor": "Credit Utilization",
                "impact": f"+{utilization_impact} points",
                "description": f"Increased total credit by ${credit_limit}"
            },
            {
                "factor": "Credit Age",
                "impact": f"{age_impact} points",
                "description": "Reduced average account age"
            }
        ])

        recommendations.append("Wait 3-6 months before applying for more credit")
        recommendations.append("Keep utilization below 30% on new card")

    elif simulation.action_type == "close_card":
        # Closing a card usually hurts score
        card_age = simulation.action_details.get("card_age_years", 5)
        credit_limit = simulation.action_details.get("credit_limit", 3000)

        # Negative: Reduced total credit
        utilization_impact = -15
        # Negative: Potentially reduced credit age
        age_impact = -5 if card_age > 5 else -2

        total_impact = utilization_impact + age_impact
        projected_score = max(300, current_score + total_impact)
        time_to_change = 1

        impact_factors.extend([
            {
                "factor": "Credit Utilization",
                "impact": f"{utilization_impact} points",
                "description": f"Reduced total credit by ${credit_limit}"
            },
            {
                "factor": "Credit History",
                "impact": f"{age_impact} points",
                "description": f"Lost {card_age} years of credit history"
            }
        ])

        recommendations.append("Consider keeping the card open with no balance")
        recommendations.append("If closing, pay down other cards first")

    # Save simulation
    simulation_record = CreditSimulation(
        user_id=current_user['user_id'],
        current_score=current_score,
        projected_score=projected_score,
        action_type=simulation.action_type,
        action_details=simulation.action_details,
        score_change=projected_score - current_score,
        time_to_change_months=time_to_change,
        impact_factors=impact_factors
    )

    db_session.add(simulation_record)
    db_session.commit()


    return CreditSimulatorResponse(
        current_score=current_score,
        projected_score=projected_score,
        score_change=projected_score - current_score,
        time_to_change_months=time_to_change,
        impact_factors=impact_factors,
        recommendations=recommendations
    )

@router.get("/tips", response_model=CreditTipsResponse)
async def get_credit_tips(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get personalized credit improvement tips"""
    # Get user's current credit score
    credit_score = db_session.query(CreditScore).filter(
        CreditScore.user_id == current_user['user_id']
    ).order_by(CreditScore.last_updated.desc()).first()

    if not credit_score:
        # Generate a score if none exists
        score_value = generate_mock_credit_score(current_user['user_id'])
    else:
        score_value = credit_score.score

    tips = []

    # Generate tips based on score range
    if score_value < 580:  # Poor
        tips.extend([
            CreditTip(
                id=1,
                title="Make All Payments On Time",
                description="Payment history is 35% of your score. Set up automatic payments to never miss a due date.",
                priority="high",
                potential_score_impact="+40-80 points",
                category=CreditFactorType.PAYMENT_HISTORY,
                action_required="Set up autopay for all accounts"
            ),
            CreditTip(
                id=2,
                title="Pay Down High Balances",
                description="High credit utilization hurts your score. Try to keep balances below 30% of limits.",
                priority="high",
                potential_score_impact="+30-50 points",
                category=CreditFactorType.CREDIT_UTILIZATION,
                action_required="Pay more than minimum on highest balance cards"
            )
        ])
    elif score_value < 670:  # Fair
        tips.extend([
            CreditTip(
                id=3,
                title="Reduce Credit Utilization",
                description="Your utilization might be too high. Aim for under 10% for best scores.",
                priority="high",
                potential_score_impact="+20-40 points",
                category=CreditFactorType.CREDIT_UTILIZATION,
                action_required="Pay down balances or request limit increases"
            ),
            CreditTip(
                id=4,
                title="Don't Close Old Cards",
                description="Keep old accounts open to maintain credit history length.",
                priority="medium",
                potential_score_impact="+10-20 points",
                category=CreditFactorType.CREDIT_AGE,
                action_required="Keep oldest cards active with small purchases"
            )
        ])
    else:  # Good or better
        tips.extend([
            CreditTip(
                id=5,
                title="Optimize Credit Mix",
                description="Having different types of credit (cards, loans) can boost your score.",
                priority="low",
                potential_score_impact="+5-15 points",
                category=CreditFactorType.CREDIT_MIX,
                action_required="Consider a small personal loan if you only have cards"
            ),
            CreditTip(
                id=6,
                title="Limit New Applications",
                description="Each application causes a small temporary dip. Space out applications.",
                priority="medium",
                potential_score_impact="+5-10 points",
                category=CreditFactorType.NEW_CREDIT,
                action_required="Wait 6+ months between credit applications"
            )
        ])

    # Add universal tips
    tips.append(
        CreditTip(
            id=7,
            title="Monitor for Errors",
            description="Check your credit report regularly for errors that could hurt your score.",
            priority="medium",
            potential_score_impact="Varies",
            category=CreditFactorType.PAYMENT_HISTORY,
            action_required="Review credit report monthly"
        )
    )

    return CreditTipsResponse(
        tips=tips,
        personalized=True,
        generated_at=datetime.utcnow()
    )

@router.get("/report", response_model=CreditReportResponse)
async def generate_credit_report(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Generate a mock credit report"""

    # Get user info
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()

    # Get credit score
    credit_score = await get_credit_score(request, CreditScoreProvider.VANTAGE, current_user, db_session)

    # Get user accounts
    accounts = db_session.query(Account).filter(
        Account.user_id == current_user['user_id']
    ).all()

    # Build mock credit accounts
    credit_accounts = []
    total_balance = 0
    total_limit = 0

    for account in accounts:
        if account.account_type.value == "credit_card":
            balance = account.balance
            limit = account.credit_limit or 5000
            total_balance += balance
            total_limit += limit

            credit_accounts.append({
                "account_name": account.name,
                "account_type": "Credit Card",
                "account_number": f"****{account.id % 10000:04d}",
                "status": "Open",
                "balance": balance,
                "credit_limit": limit,
                "payment_status": "Current",
                "opened_date": account.created_at.isoformat()
            })

    # Calculate utilization
    utilization = (total_balance / total_limit * 100) if total_limit > 0 else 0

    # Mock payment history
    payment_history = {
        "on_time_payments": 95,
        "late_payments": 2,
        "missed_payments": 0,
        "months_reviewed": 24
    }

    # Mock inquiries
    inquiries = [
        {
            "creditor": "Example Bank",
            "date": (datetime.utcnow() - timedelta(days=45)).isoformat(),
            "type": "Hard Inquiry"
        }
    ]

    # Generate report
    return CreditReportResponse(
        report_id=f"CR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.utcnow(),
        user_info={
            "name": f"{user.first_name} {user.last_name}",
            "current_address": "123 Main St, Anytown, USA",  # Mock
            "date_of_birth": "**/**/****",  # Masked
            "ssn": "***-**-****"  # Masked
        },
        credit_score=credit_score.score,
        accounts=credit_accounts,
        payment_history=payment_history,
        credit_utilization=round(utilization, 1),
        credit_inquiries=inquiries,
        public_records=[],  # No bankruptcies, liens, etc.
        collections=[],  # No collections
        score_factors=credit_score.factors
    )

    # Log report generation



# Credit Alert Endpoints

@router.get("/alerts")
async def get_credit_alerts(
    request: Request,
    include_dismissed: bool = False,
    alert_type: str | None = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get credit monitoring alerts for the user"""
    query = db_session.query(CreditAlert).filter(
        CreditAlert.user_id == current_user['user_id']
    )

    if not include_dismissed:
        query = query.filter(not CreditAlert.is_dismissed)

    if alert_type:
        query = query.filter(CreditAlert.alert_type == alert_type)

    alerts = query.order_by(CreditAlert.alert_date.desc()).all()

    # Convert to dict format
    alerts_data = []
    for alert in alerts:
        alert_dict = alert.to_dict()
        alerts_data.append(alert_dict)

    return {"alerts": alerts_data, "total": len(alerts_data)}


@router.post("/alerts")
async def create_credit_alert(
    request: Request,
    alert_data: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new credit alert (admin/system use)"""

    # Create new alert
    alert = CreditAlert(
        user_id=current_user['user_id'],
        alert_type=alert_data.get('alert_type', 'score_change'),
        severity=alert_data.get('severity', 'info'),
        title=alert_data['title'],
        description=alert_data['description'],
        action_required=alert_data.get('action_required', False),
        action_url=alert_data.get('action_url'),
        metadata=alert_data.get('metadata', {})
    )

    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    # Log alert creation

    return {"message": "Alert created successfully", "alert": alert.to_dict()}


@router.put("/alerts/{alert_id}")
async def update_alert_status(
    alert_id: int,
    status_update: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update alert status (mark as read/dismissed)"""
    alert = db_session.query(CreditAlert).filter(
        CreditAlert.id == alert_id,
        CreditAlert.user_id == current_user['user_id']
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if 'is_read' in status_update:
        alert.is_read = status_update['is_read']

    if 'is_dismissed' in status_update:
        alert.is_dismissed = status_update['is_dismissed']

    db_session.commit()
    db_session.refresh(alert)

    return {"message": "Alert updated", "alert": alert.to_dict()}


# Credit Dispute Endpoints

@router.get("/disputes")
async def get_credit_disputes(
    status: str | None = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all credit disputes for the user"""
    query = db_session.query(CreditDispute).filter(
        CreditDispute.user_id == current_user['user_id']
    )

    if status:
        query = query.filter(CreditDispute.status == status)

    disputes = query.order_by(CreditDispute.filed_date.desc()).all()

    disputes_data = []
    for dispute in disputes:
        dispute_dict = dispute.to_dict()
        disputes_data.append(dispute_dict)

    return {"disputes": disputes_data, "total": len(disputes_data)}


@router.post("/disputes")
async def create_credit_dispute(
    request: Request,
    dispute_data: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """File a new credit dispute"""

    # Create new dispute
    dispute = CreditDispute(
        user_id=current_user['user_id'],
        dispute_type=dispute_data['dispute_type'],
        bureau=dispute_data['bureau'],
        account_name=dispute_data['account_name'],
        dispute_reason=dispute_data['dispute_reason'],
        dispute_details=dispute_data.get('dispute_details', ''),
        supporting_documents=dispute_data.get('supporting_documents', [])
    )

    db_session.add(dispute)
    db_session.commit()
    db_session.refresh(dispute)

    # Create an alert for the new dispute
    alert = CreditAlert(
        user_id=current_user['user_id'],
        alert_type='dispute_update',
        severity='info',
        title='Credit Dispute Filed',
        description=f'Your dispute with {dispute.bureau} has been filed successfully',
        action_required=False,
        metadata={'dispute_id': dispute.id}
    )

    db_session.add(alert)
    db_session.commit()

    # Log dispute creation

    return {"message": "Dispute filed successfully", "dispute": dispute.to_dict()}


@router.put("/disputes/{dispute_id}")
async def update_dispute_status(
    request: Request,
    dispute_id: int,
    status_update: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update dispute status"""

    dispute = db_session.query(CreditDispute).filter(
        CreditDispute.id == dispute_id,
        CreditDispute.user_id == current_user['user_id']
    ).first()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    # Update fields
    if 'status' in status_update:
        dispute.status = status_update['status']

    if 'bureau_response' in status_update:
        dispute.bureau_response = status_update['bureau_response']

    if 'outcome' in status_update:
        dispute.outcome = status_update['outcome']
        if dispute.outcome in ['removed', 'corrected']:
            dispute.resolution_date = datetime.utcnow()

    dispute.last_updated = datetime.utcnow()

    db_session.commit()
    db_session.refresh(dispute)

    # Create alert for status change
    alert = CreditAlert(
        user_id=current_user['user_id'],
        alert_type='dispute_update',
        severity='warning' if dispute.status == 'resolved' else 'info',
        title=f'Dispute Status Updated: {dispute.status.title()}',
        description=f'Your dispute with {dispute.bureau} has been updated',
        action_required=dispute.status == 'resolved',
        action_url=f'/credit/disputes/{dispute_id}',
        metadata={'dispute_id': dispute.id, 'new_status': dispute.status}
    )

    db_session.add(alert)
    db_session.commit()

    # Log update

    return {"message": "Dispute updated", "dispute": dispute.to_dict()}


# Credit Builder Endpoints

@router.get("/credit-builder")
async def get_credit_builder_accounts(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all credit builder accounts for the user"""
    accounts = db_session.query(CreditBuilderAccount).filter(
        CreditBuilderAccount.user_id == current_user['user_id']
    ).order_by(CreditBuilderAccount.opened_date.desc()).all()

    accounts_data = []
    for account in accounts:
        account_dict = account.to_dict()
        # Calculate utilization
        if account.credit_limit > 0:
            account_dict['utilization'] = round((account.current_balance / account.credit_limit) * 100, 1)
        else:
            account_dict['utilization'] = 0
        accounts_data.append(account_dict)

    return {"accounts": accounts_data, "total": len(accounts_data)}


@router.post("/credit-builder")
async def create_credit_builder_account(
    request: Request,
    account_data: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new credit builder account"""

    # Create credit builder account
    account = CreditBuilderAccount(
        user_id=current_user['user_id'],
        account_type=account_data['account_type'],
        secured_amount=account_data['secured_amount'],
        credit_limit=account_data.get('credit_limit', account_data['secured_amount']),
        auto_pay_enabled=account_data.get('auto_pay_enabled', False),
        monthly_fee=account_data.get('monthly_fee', 0.0)
    )

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Create alert for new account
    alert = CreditAlert(
        user_id=current_user['user_id'],
        alert_type='new_account',
        severity='info',
        title='Credit Builder Account Opened',
        description=f'Your {account.account_type} has been opened successfully',
        action_required=True,
        action_url='/credit/credit-builder',
        metadata={'account_id': account.id, 'account_type': account.account_type}
    )

    db_session.add(alert)
    db_session.commit()

    # Log account creation

    return {"message": "Credit builder account created", "account": account.to_dict()}


@router.post("/credit-builder/{account_id}/payment")
async def make_credit_builder_payment(
    request: Request,
    account_id: int,
    payment_data: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Make a payment on credit builder account"""

    account = db_session.query(CreditBuilderAccount).filter(
        CreditBuilderAccount.id == account_id,
        CreditBuilderAccount.user_id == current_user['user_id']
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Process payment
    payment_amount = payment_data['amount']
    account.current_balance = max(0, account.current_balance - payment_amount)
    account.last_payment_date = datetime.utcnow()

    # Add to payment history
    payment_record = {
        'date': datetime.utcnow().isoformat(),
        'amount': payment_amount,
        'on_time': payment_data.get('on_time', True)
    }

    if not account.payment_history:
        account.payment_history = []
    account.payment_history.append(payment_record)

    # Check for graduation eligibility
    if len(account.payment_history) >= 12:
        on_time_payments = sum(1 for p in account.payment_history[-12:] if p.get('on_time', True))
        if on_time_payments >= 11:  # 11 out of 12 on-time
            account.graduation_eligible = True

    db_session.commit()
    db_session.refresh(account)

    # Create payment alert
    alert = CreditAlert(
        user_id=current_user['user_id'],
        alert_type='payment_reported',
        severity='info',
        title='Payment Reported to Credit Bureaus',
        description=f'Your ${payment_amount} payment has been reported',
        action_required=False,
        metadata={'account_id': account.id, 'payment_amount': payment_amount}
    )

    db_session.add(alert)
    db_session.commit()

    # Log payment

    return {
        "message": "Payment processed successfully",
        "account": account.to_dict(),
        "graduation_eligible": account.graduation_eligible
    }


@router.post("/monitoring/simulate-change")
async def simulate_credit_change(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Simulate a credit score change for demo purposes"""

    # Get current score
    credit_score = db_session.query(CreditScore).filter(
        CreditScore.user_id == current_user['user_id']
    ).order_by(CreditScore.last_updated.desc()).first()

    if not credit_score:
        return {"error": "No credit score found"}

    # Simulate a change
    old_score = credit_score.score
    change = random.choice([-15, -10, -5, 5, 10, 15, 20])
    new_score = max(300, min(850, old_score + change))

    # Update score
    credit_score.score = new_score
    credit_score.score_range = calculate_credit_score_range(new_score)
    credit_score.last_updated = datetime.utcnow()

    # Create alert
    severity = 'critical' if change <= -10 else 'warning' if change < 0 else 'info'
    alert = CreditAlert(
        user_id=current_user['user_id'],
        alert_type='score_change',
        severity=severity,
        title=f'Credit Score {"Decreased" if change < 0 else "Increased"} by {abs(change)} Points',
        description=f'Your {credit_score.provider} score changed from {old_score} to {new_score}',
        action_required=change < 0,
        action_url='/credit/score',
        metadata={
            'old_score': old_score,
            'new_score': new_score,
            'change': change,
            'provider': credit_score.provider
        }
    )

    db_session.add(alert)
    db_session.commit()

    # Log simulation

    return {
        "message": "Credit change simulated",
        "old_score": old_score,
        "new_score": new_score,
        "change": change,
        "alert": alert.to_dict()
    }
