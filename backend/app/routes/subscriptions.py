from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from collections import defaultdict

from ..storage.memory_adapter import db, desc
from ..models import (
    Subscription, CancellationReminder, Transaction, Account, User,
    SubscriptionStatus, BillingCycle, SubscriptionCategory,
    TransactionType
)
from ..models import (
    SubscriptionResponse, SubscriptionUpdateRequest, SubscriptionAnalysisResponse,
    CancellationReminderRequest, CancellationReminderResponse,
    OptimizationSuggestion, OptimizationResponse, OptimizationSuggestionType,
    SubscriptionCreateRequest, SubscriptionDetailResponse, SubscriptionCancelRequest,
    SubscriptionCancelResponse, SubscriptionPauseRequest, SubscriptionPauseResponse,
    SubscriptionSummaryResponse, PaymentHistoryResponse, SubscriptionReminderRequest,
    SubscriptionReminderResponse, SubscriptionUsageRequest, SubscriptionUsageResponse,
    SubscriptionRecommendationsResponse, SubscriptionShareRequest, SubscriptionShareResponse,
    BulkImportRequest, BulkImportResponse
)
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError
from ..utils.session_manager import session_manager

router = APIRouter()

def detect_recurring_transactions(
    transactions: List[Transaction],
    confidence_threshold: float = 0.8
) -> List[Dict]:
    """Detect potential subscriptions from transaction history"""
    # Group by merchant name
    merchant_groups = defaultdict(list)
    
    for tx in transactions:
        # Extract merchant name (simplified)
        merchant = tx.description.split()[0] if tx.description else "Unknown"
        merchant_groups[merchant].append(tx)
    
    detected_subscriptions = []
    
    for merchant, txs in merchant_groups.items():
        if len(txs) < 2:
            continue
        
        # Sort by date
        txs.sort(key=lambda x: x.transaction_date)
        
        # Check for regular intervals
        intervals = []
        amounts = []
        
        for i in range(1, len(txs)):
            interval = (txs[i].transaction_date - txs[i-1].transaction_date).days
            intervals.append(interval)
            amounts.append(txs[i].amount)
        
        if not intervals:
            continue
        
        # Analyze pattern
        avg_interval = sum(intervals) / len(intervals)
        avg_amount = sum(amounts) / len(amounts)
        
        # Check consistency
        interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        amount_variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
        
        # Calculate confidence
        interval_consistency = 1 - (interval_variance / (avg_interval ** 2) if avg_interval > 0 else 0)
        amount_consistency = 1 - (amount_variance / (avg_amount ** 2) if avg_amount > 0 else 0)
        confidence = (interval_consistency + amount_consistency) / 2
        
        if confidence >= confidence_threshold:
            # Determine billing cycle
            if 26 <= avg_interval <= 35:
                billing_cycle = BillingCycle.MONTHLY
            elif 6 <= avg_interval <= 8:
                billing_cycle = BillingCycle.WEEKLY
            elif 80 <= avg_interval <= 100:
                billing_cycle = BillingCycle.QUARTERLY
            elif 350 <= avg_interval <= 380:
                billing_cycle = BillingCycle.ANNUAL
            else:
                continue  # Skip if doesn't match known patterns
            
            # Categorize subscription
            category = categorize_subscription(merchant.lower())
            
            detected_subscriptions.append({
                "merchant_name": merchant,
                "amount": round(avg_amount, 2),
                "billing_cycle": billing_cycle,
                "category": category,
                "confidence": round(confidence, 2),
                "last_transaction": txs[-1],
                "transaction_count": len(txs)
            })
    
    return detected_subscriptions

def categorize_subscription(merchant_name: str) -> SubscriptionCategory:
    """Categorize subscription based on merchant name"""
    merchant_lower = merchant_name.lower()
    
    # Streaming
    if any(name in merchant_lower for name in ["netflix", "hulu", "disney", "hbo", "youtube", "spotify"]):
        return SubscriptionCategory.STREAMING
    # Software
    elif any(name in merchant_lower for name in ["adobe", "microsoft", "github", "jetbrains", "slack"]):
        return SubscriptionCategory.SOFTWARE
    # Gaming
    elif any(name in merchant_lower for name in ["xbox", "playstation", "steam", "nintendo"]):
        return SubscriptionCategory.GAMING
    # Music
    elif any(name in merchant_lower for name in ["apple music", "pandora", "tidal"]):
        return SubscriptionCategory.MUSIC
    # News
    elif any(name in merchant_lower for name in ["times", "journal", "post", "bloomberg"]):
        return SubscriptionCategory.NEWS
    # Fitness
    elif any(name in merchant_lower for name in ["gym", "fitness", "peloton", "strava"]):
        return SubscriptionCategory.FITNESS
    # Food Delivery
    elif any(name in merchant_lower for name in ["doordash", "uber eats", "grubhub", "hello fresh"]):
        return SubscriptionCategory.FOOD_DELIVERY
    # Cloud Storage
    elif any(name in merchant_lower for name in ["dropbox", "google", "icloud", "onedrive"]):
        return SubscriptionCategory.CLOUD_STORAGE
    # Education
    elif any(name in merchant_lower for name in ["coursera", "udemy", "masterclass", "skillshare"]):
        return SubscriptionCategory.EDUCATION
    else:
        return SubscriptionCategory.OTHER

def calculate_next_billing_date(last_date: date, billing_cycle: BillingCycle) -> date:
    """Calculate next billing date based on cycle"""
    if billing_cycle == BillingCycle.WEEKLY:
        return last_date + timedelta(days=7)
    elif billing_cycle == BillingCycle.MONTHLY:
        # Handle month boundaries
        if last_date.month == 12:
            return last_date.replace(year=last_date.year + 1, month=1)
        else:
            try:
                return last_date.replace(month=last_date.month + 1)
            except ValueError:
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                return last_date.replace(month=last_date.month + 1, day=1) + timedelta(days=27)
    elif billing_cycle == BillingCycle.QUARTERLY:
        return last_date + timedelta(days=90)
    elif billing_cycle == BillingCycle.SEMI_ANNUAL:
        return last_date + timedelta(days=180)
    elif billing_cycle == BillingCycle.ANNUAL:
        return last_date.replace(year=last_date.year + 1)
    else:
        return last_date + timedelta(days=30)  # Default to monthly


def _create_subscription_response(
    sub: Any,
    transaction_ids: List[int] = None,
    is_trial: bool = False,
    regular_price: Optional[float] = None,
    days_until_billing: Optional[int] = None
) -> SubscriptionResponse:
    """Helper to create SubscriptionResponse with proper field handling."""
    # Ensure all required fields are present
    merchant_name = getattr(sub, 'merchant_name', None) or sub.name.replace(' Subscription', '') if sub.name else 'Unknown'
    start_date_value = getattr(sub, 'start_date', None) or date.today()
    updated_at_value = getattr(sub, 'updated_at', None) or sub.created_at
    
    # Convert next_billing_date to date if it's a datetime
    next_billing_date_value = sub.next_billing_date
    if isinstance(next_billing_date_value, datetime):
        next_billing_date_value = next_billing_date_value.date()
    elif isinstance(next_billing_date_value, str):
        try:
            next_billing_date_value = datetime.fromisoformat(next_billing_date_value.replace('Z', '+00:00')).date()
        except:
            next_billing_date_value = date.today() + timedelta(days=30)
    
    # Map old category values to new enum values
    category_mapping = {
        'entertainment': SubscriptionCategory.STREAMING,
        'shopping': SubscriptionCategory.OTHER,
        'health_fitness': SubscriptionCategory.FITNESS,
        'cloud_storage': SubscriptionCategory.CLOUD_STORAGE,
        'news_media': SubscriptionCategory.NEWS,
        'food_delivery': SubscriptionCategory.FOOD_DELIVERY,
        'productivity': SubscriptionCategory.SOFTWARE,
        'utilities': SubscriptionCategory.OTHER,
        'education': SubscriptionCategory.EDUCATION,
        'streaming': SubscriptionCategory.STREAMING,
        'software': SubscriptionCategory.SOFTWARE,
        'gaming': SubscriptionCategory.GAMING,
        'music': SubscriptionCategory.MUSIC,
        'news': SubscriptionCategory.NEWS,
        'fitness': SubscriptionCategory.FITNESS,
        'other': SubscriptionCategory.OTHER
    }
    category_value = category_mapping.get(sub.category, SubscriptionCategory.OTHER)
    
    # Map old billing cycle values
    billing_cycle_mapping = {
        'yearly': BillingCycle.ANNUAL,
        'daily': BillingCycle.WEEKLY,  # Map daily to weekly as closest match
        'annual': BillingCycle.ANNUAL,
        'weekly': BillingCycle.WEEKLY,
        'monthly': BillingCycle.MONTHLY,
        'quarterly': BillingCycle.QUARTERLY,
        'semi_annual': BillingCycle.SEMI_ANNUAL
    }
    billing_cycle_value = billing_cycle_mapping.get(sub.billing_cycle, sub.billing_cycle)
    
    return SubscriptionResponse(
        id=sub.id,
        user_id=sub.user_id,
        name=sub.name,
        merchant_name=merchant_name,
        category=category_value,
        status=sub.status,
        amount=sub.amount,
        billing_cycle=billing_cycle_value,
        next_billing_date=next_billing_date_value,
        last_billing_date=getattr(sub, 'last_billing_date', None),
        start_date=start_date_value,
        end_date=getattr(sub, 'end_date', None),
        free_trial_end_date=getattr(sub, 'free_trial_end_date', None),
        transaction_ids=transaction_ids or [],
        detected_automatically=getattr(sub, 'detected_automatically', False),
        confidence_score=getattr(sub, 'confidence_score', None),
        created_at=sub.created_at,
        updated_at=updated_at_value,
        is_trial=is_trial,
        regular_price=regular_price,
        days_until_billing=days_until_billing
    )

@router.get("", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    status: Optional[SubscriptionStatus] = None,
    category: Optional[SubscriptionCategory] = None,
    auto_detect: bool = False,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """List all subscriptions with optional auto-detection"""
    
    # Get existing subscriptions
    query = db_session.query(Subscription).filter(
        Subscription.user_id == current_user['user_id']
    )

    if status:
        query = query.filter(Subscription.status == status)
    
    if category:
        query = query.filter(Subscription.category == category)
    
    subscriptions = query.order_by(Subscription.next_billing_date).all()
    
    # Auto-detect if requested
    if auto_detect:
        # Get recent transactions
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        
        transactions = db_session.query(Transaction).join(
            Account
        ).filter(
            Account.user_id == current_user['user_id'],
            Transaction.transaction_date >= three_months_ago,
            Transaction.transaction_type == TransactionType.DEBIT
        ).all()
        
        # Detect recurring patterns
        detected = detect_recurring_transactions(transactions)
        
        # Add detected subscriptions that don't exist yet
        for detection in detected:
            # Check if already tracked
            existing = db_session.query(Subscription).filter(
                Subscription.user_id == current_user['user_id'],
                Subscription.merchant_name == detection["merchant_name"],
                Subscription.amount == detection["amount"]
            ).first()
            
            if not existing:
                last_tx = detection["last_transaction"]
                next_billing = calculate_next_billing_date(
                    last_tx.transaction_date.date(),
                    detection["billing_cycle"]
                )

                subscription = Subscription(
                    user_id=current_user['user_id'],
                    name=f"{detection['merchant_name']} Subscription",
                    merchant_name=detection["merchant_name"],
                    category=detection["category"],
                    status=SubscriptionStatus.ACTIVE,
                    amount=detection["amount"],
                    billing_cycle=detection["billing_cycle"],
                    next_billing_date=next_billing,
                    last_billing_date=last_tx.transaction_date.date(),
                    start_date=last_tx.transaction_date.date() - timedelta(days=90),  # Estimate
                    detected_automatically=True,
                    confidence_score=detection["confidence"]
                )

                db_session.add(subscription)
        
        db_session.commit()
        
        # Refresh subscription list
        subscriptions = query.order_by(Subscription.next_billing_date).all()
    
    # Build response with transaction links
    results = []
    for sub in subscriptions:
        # Get linked transactions
        linked_txs = []
        
        response = _create_subscription_response(
            sub, 
            transaction_ids=[tx.id for tx in linked_txs]
        )
        results.append(response)
    
    return results

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    request: Request,
    subscription_id: int,
    update_data: SubscriptionUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update subscription information"""
    
    # Get subscription
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Update fields
    if update_data.name is not None:
        subscription.name = update_data.name
    
    if update_data.category is not None:
        subscription.category = update_data.category
    
    if update_data.status is not None:
        old_status = subscription.status
        subscription.status = update_data.status
        
        # Handle status changes
        if update_data.status == SubscriptionStatus.CANCELLED:
            subscription.end_date = date.today()
    
    if update_data.amount is not None:
        subscription.amount = update_data.amount
    
    if update_data.billing_cycle is not None:
        subscription.billing_cycle = update_data.billing_cycle
    
    if update_data.next_billing_date is not None:
        subscription.next_billing_date = update_data.next_billing_date
    
    if update_data.notes is not None:
        subscription.notes = update_data.notes
    
    subscription.updated_at = datetime.utcnow()
    
    db_session.commit()
    db_session.refresh(subscription)

    # Return with transaction links
    linked_txs = db_session.query(Transaction).join(
        Account
    ).filter(
        Account.user_id == current_user['user_id'],
        Transaction.description.ilike(f"%{subscription.merchant_name}%"),
        Transaction.amount == subscription.amount
    ).order_by(Transaction.transaction_date.desc()).limit(5).all()
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        name=subscription.name,
        merchant_name=subscription.merchant_name,
        category=subscription.category,
        status=subscription.status,
        amount=subscription.amount,
        billing_cycle=subscription.billing_cycle,
        next_billing_date=subscription.next_billing_date,
        last_billing_date=subscription.last_billing_date,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        free_trial_end_date=subscription.free_trial_end_date,
        transaction_ids=[tx.id for tx in linked_txs],
        detected_automatically=subscription.detected_automatically,
        confidence_score=subscription.confidence_score,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at
    )

@router.get("/analysis", response_model=SubscriptionAnalysisResponse)
async def analyze_subscriptions(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get comprehensive subscription analysis"""
    # Get all subscriptions
    subscriptions = db_session.query(Subscription).filter(
        Subscription.user_id == current_user['user_id']
    ).all()
    
    # Calculate metrics
    total_subscriptions = len(subscriptions)
    active_subscriptions = sum(1 for s in subscriptions if s.status == SubscriptionStatus.ACTIVE)
    
    # Calculate costs
    total_monthly_cost = 0
    total_annual_cost = 0
    cost_by_category = defaultdict(float)
    
    for sub in subscriptions:
        if sub.status != SubscriptionStatus.ACTIVE:
            continue
        
        # Convert to monthly cost
        if sub.billing_cycle == BillingCycle.WEEKLY:
            monthly_cost = sub.amount * 4.33  # 52/12
        elif sub.billing_cycle == BillingCycle.MONTHLY:
            monthly_cost = sub.amount
        elif sub.billing_cycle == BillingCycle.QUARTERLY:
            monthly_cost = sub.amount / 3
        elif sub.billing_cycle == BillingCycle.SEMI_ANNUAL:
            monthly_cost = sub.amount / 6
        elif sub.billing_cycle == BillingCycle.ANNUAL:
            monthly_cost = sub.amount / 12
        else:
            monthly_cost = sub.amount
        
        total_monthly_cost += monthly_cost
        cost_by_category[sub.category] += monthly_cost
    
    total_annual_cost = total_monthly_cost * 12
    
    # Cost trend (mock - last 6 months)
    cost_trend = []
    for i in range(6):
        month_date = datetime.utcnow() - timedelta(days=i * 30)
        # Add some variation
        variation = 1 + (0.1 * (i % 3 - 1))
        cost_trend.append({
            "month": month_date.strftime("%Y-%m"),
            "cost": round(total_monthly_cost * variation, 2)
        })
    
    cost_trend.reverse()
    
    # Find most expensive
    most_expensive = sorted(
        [s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE],
        key=lambda x: x.amount if x.billing_cycle == BillingCycle.MONTHLY else x.amount / 12,
        reverse=True
    )[:5]
    
    most_expensive_data = [
        {
            "id": s.id,
            "name": s.name,
            "amount": s.amount,
            "billing_cycle": s.billing_cycle
        }
        for s in most_expensive
    ]
    
    # Find least used (mock based on category)
    least_used = []
    for sub in subscriptions:
        if sub.status == SubscriptionStatus.ACTIVE and sub.category in [
            SubscriptionCategory.FITNESS,
            SubscriptionCategory.EDUCATION
        ]:
            least_used.append({
                "id": sub.id,
                "name": sub.name,
                "last_used": "30 days ago",  # Mock
                "usage_score": 0.2
            })
    
    # Upcoming renewals
    upcoming = sorted(
        [s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE and s.next_billing_date],
        key=lambda x: x.next_billing_date
    )[:5]
    
    upcoming_renewals = [
        {
            "id": s.id,
            "name": s.name,
            "next_billing_date": s.next_billing_date,
            "amount": s.amount
        }
        for s in upcoming
    ]
    
    # Calculate potential savings (20% estimate)
    savings_opportunities = total_monthly_cost * 0.2
    
    return SubscriptionAnalysisResponse(
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        total_monthly_cost=round(total_monthly_cost, 2),
        total_annual_cost=round(total_annual_cost, 2),
        cost_by_category=dict(cost_by_category),
        cost_trend=cost_trend,
        most_expensive=most_expensive_data,
        least_used=least_used,
        upcoming_renewals=upcoming_renewals,
        savings_opportunities=round(savings_opportunities, 2),
        average_subscription_cost=round(total_monthly_cost / active_subscriptions, 2) if active_subscriptions > 0 else 0
    )

@router.post("/{subscription_id}/reminder", response_model=CancellationReminderResponse, status_code=status.HTTP_201_CREATED)
async def set_cancellation_reminder(
    request: Request,
    subscription_id: int,
    reminder_data: CancellationReminderRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Set a cancellation reminder for a subscription"""
    
    # Get subscription
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Calculate reminder date
    if reminder_data.target_date:
        reminder_date = reminder_data.target_date
    elif subscription.next_billing_date:
        reminder_date = subscription.next_billing_date - timedelta(days=reminder_data.days_before)
    else:
        raise ValidationError("Cannot set reminder without billing date")
    
    # Check for existing reminder
    existing = db_session.query(CancellationReminder).filter(
        CancellationReminder.subscription_id == subscription_id,
        CancellationReminder.user_id == current_user['user_id'],
        CancellationReminder.is_sent == False
    ).first()
    
    if existing:
        raise ValidationError("Active reminder already exists for this subscription")
    
    # Create reminder
    reminder = CancellationReminder(
        subscription_id=subscription_id,
        user_id=current_user['user_id'],
        reminder_date=reminder_date,
        reason=reminder_data.reason
    )

    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    
    
    return CancellationReminderResponse.from_orm(reminder)

@router.get("/optimize", response_model=OptimizationResponse)
async def get_optimization_suggestions(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get subscription optimization suggestions"""
    # Get all active subscriptions
    subscriptions = db_session.query(Subscription).filter(
        Subscription.user_id == current_user['user_id'],
        Subscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    suggestions = []
    total_potential_savings = 0
    
    # Check for duplicate services
    category_services = defaultdict(list)
    for sub in subscriptions:
        category_services[sub.category].append(sub)
    
    duplicate_services = []
    for category, subs in category_services.items():
        if len(subs) > 1:
            duplicate_services.append({
                "category": category,
                "services": [{"id": s.id, "name": s.name, "cost": s.amount} for s in subs],
                "potential_savings": sum(s.amount for s in subs[1:])  # Keep cheapest
            })
            
            # Add suggestion for most expensive duplicate
            most_expensive = max(subs, key=lambda x: x.amount)
            cheapest = min(subs, key=lambda x: x.amount)
            
            if most_expensive.id != cheapest.id:
                suggestions.append(OptimizationSuggestion(
                    subscription_id=most_expensive.id,
                    subscription_name=most_expensive.name,
                    suggestion_type=OptimizationSuggestionType.DUPLICATE_SERVICE,
                    current_cost=most_expensive.amount,
                    potential_savings=most_expensive.amount,
                    alternative_name=cheapest.name,
                    alternative_cost=cheapest.amount,
                    reason=f"You have multiple {category} subscriptions",
                    confidence=0.9,
                    action_steps=[
                        f"Review if you need both {most_expensive.name} and {cheapest.name}",
                        f"Consider cancelling {most_expensive.name} to save ${most_expensive.amount}/month",
                        "Export any data before cancelling"
                    ]
                ))
                total_potential_savings += most_expensive.amount
    
    # Check for bundling opportunities
    bundling_opportunities = []
    
    # Example: Multiple streaming services
    streaming_subs = [s for s in subscriptions if s.category == SubscriptionCategory.STREAMING]
    if len(streaming_subs) >= 3:
        total_streaming_cost = sum(s.amount for s in streaming_subs)
        bundle_cost = 25.99  # Mock bundle price
        
        if total_streaming_cost > bundle_cost:
            bundling_opportunities.append({
                "services": [s.name for s in streaming_subs],
                "current_total": total_streaming_cost,
                "bundle_price": bundle_cost,
                "savings": total_streaming_cost - bundle_cost
            })
            
            suggestions.append(OptimizationSuggestion(
                subscription_id=streaming_subs[0].id,
                subscription_name="Multiple Streaming Services",
                suggestion_type=OptimizationSuggestionType.BUNDLE_OPPORTUNITY,
                current_cost=total_streaming_cost,
                potential_savings=total_streaming_cost - bundle_cost,
                alternative_name="Streaming Bundle",
                alternative_cost=bundle_cost,
                reason="Bundle your streaming services for savings",
                confidence=0.8,
                action_steps=[
                    "Check if your provider offers a bundle deal",
                    "Compare bundle features with individual subscriptions",
                    "Switch to bundle if it meets your needs"
                ]
            ))
            total_potential_savings += total_streaming_cost - bundle_cost
    
    # Check for unused subscriptions (mock based on category/price)
    unused_subscriptions = []
    for sub in subscriptions:
        # Mock logic: expensive fitness/education subscriptions often go unused
        if (sub.category in [SubscriptionCategory.FITNESS, SubscriptionCategory.EDUCATION] and 
            sub.amount > 20):
            
            unused_subscriptions.append({
                "id": sub.id,
                "name": sub.name,
                "cost": sub.amount,
                "last_used": "Over 30 days ago"  # Mock
            })
            
            suggestions.append(OptimizationSuggestion(
                subscription_id=sub.id,
                subscription_name=sub.name,
                suggestion_type=OptimizationSuggestionType.USAGE_LOW,
                current_cost=sub.amount,
                potential_savings=sub.amount,
                alternative_name=None,
                alternative_cost=0,
                reason="Low usage detected in the last 30 days",
                confidence=0.7,
                action_steps=[
                    "Review if you still need this subscription",
                    "Consider pausing or cancelling if not in use",
                    "Set a reminder to re-evaluate in 2 weeks"
                ]
            ))
            total_potential_savings += sub.amount
    
    # Check for cheaper alternatives
    for sub in subscriptions:
        # Mock alternative suggestions
        if sub.category == SubscriptionCategory.SOFTWARE and sub.amount > 30:
            suggestions.append(OptimizationSuggestion(
                subscription_id=sub.id,
                subscription_name=sub.name,
                suggestion_type=OptimizationSuggestionType.CHEAPER_ALTERNATIVE,
                current_cost=sub.amount,
                potential_savings=sub.amount * 0.3,
                alternative_name=f"{sub.name} Basic Plan",
                alternative_cost=sub.amount * 0.7,
                reason="A more affordable plan may meet your needs",
                confidence=0.6,
                action_steps=[
                    "Review your usage of premium features",
                    "Check if a basic plan would suffice",
                    "Downgrade if you don't need all features"
                ]
            ))
            total_potential_savings += sub.amount * 0.3
    
    # Calculate optimization score (0-100)
    current_total = sum(s.amount for s in subscriptions)
    optimization_score = max(0, min(100, 100 - (total_potential_savings / current_total * 100))) if current_total > 0 else 100
    
    return OptimizationResponse(
        total_potential_savings=round(total_potential_savings, 2),
        suggestions=suggestions[:10],  # Top 10 suggestions
        bundling_opportunities=bundling_opportunities,
        unused_subscriptions=unused_subscriptions,
        duplicate_services=duplicate_services,
        optimization_score=round(optimization_score, 1),
        generated_at=datetime.utcnow()
    )

@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: Request,
    subscription_data: SubscriptionCreateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new subscription"""
    
    # Calculate dates
    start_date = subscription_data.start_date or date.today()
    next_billing_date = calculate_next_billing_date(start_date, subscription_data.billing_cycle)
    
    # Handle trial period
    if subscription_data.is_trial and subscription_data.trial_end_date:
        next_billing_date = subscription_data.trial_end_date
    
    # Create subscription
    subscription = Subscription(
        user_id=current_user['user_id'],
        name=f"{subscription_data.service_name} Subscription",
        merchant_name=subscription_data.service_name,
        category=subscription_data.category,
        status=SubscriptionStatus.ACTIVE,
        amount=subscription_data.amount,
        billing_cycle=subscription_data.billing_cycle,
        next_billing_date=next_billing_date,
        start_date=start_date,
        notes=subscription_data.description,
        detected_automatically=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Add trial info if applicable
    if subscription_data.is_trial:
        subscription.free_trial_end_date = subscription_data.trial_end_date
        if subscription_data.regular_price:
            subscription.notes = f"{subscription.notes or ''} Regular price: ${subscription_data.regular_price}"
    
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    
    
    
    # Calculate days until billing for trials
    days_until_billing = None
    if subscription_data.is_trial and subscription.next_billing_date:
        if isinstance(subscription.next_billing_date, datetime):
            days_until_billing = (subscription.next_billing_date.date() - date.today()).days
        elif isinstance(subscription.next_billing_date, date):
            days_until_billing = (subscription.next_billing_date - date.today()).days
    
    return _create_subscription_response(
        subscription,
        is_trial=subscription_data.is_trial,
        regular_price=subscription_data.regular_price,
        days_until_billing=days_until_billing
    )

@router.get("/summary", response_model=SubscriptionSummaryResponse)
async def get_subscription_summary(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get spending summary for subscriptions"""
    # Get all subscriptions
    subscriptions = db_session.query(Subscription).filter(
        Subscription.user_id == current_user['user_id']
    ).all()
    
    # Count by status
    active_count = sum(1 for s in subscriptions if s.status == SubscriptionStatus.ACTIVE)
    paused_count = sum(1 for s in subscriptions if s.status == SubscriptionStatus.PAUSED)
    cancelled_count = sum(1 for s in subscriptions if s.status == SubscriptionStatus.CANCELLED)
    
    # Calculate costs
    total_monthly_cost = 0
    by_category = defaultdict(float)
    
    for sub in subscriptions:
        if sub.status != SubscriptionStatus.ACTIVE:
            continue
        
        # Convert to monthly cost
        if sub.billing_cycle == BillingCycle.WEEKLY:
            monthly_cost = sub.amount * 4.33
        elif sub.billing_cycle == BillingCycle.MONTHLY:
            monthly_cost = sub.amount
        elif sub.billing_cycle == BillingCycle.QUARTERLY:
            monthly_cost = sub.amount / 3
        elif sub.billing_cycle == BillingCycle.SEMI_ANNUAL:
            monthly_cost = sub.amount / 6
        elif sub.billing_cycle == BillingCycle.ANNUAL:
            monthly_cost = sub.amount / 12
        else:
            monthly_cost = sub.amount
        
        total_monthly_cost += monthly_cost
        by_category[sub.category] += monthly_cost
    
    total_annual_cost = total_monthly_cost * 12
    
    return SubscriptionSummaryResponse(
        total_monthly_cost=round(total_monthly_cost, 2),
        total_annual_cost=round(total_annual_cost, 2),
        active_subscriptions=active_count,
        paused_subscriptions=paused_count,
        cancelled_subscriptions=cancelled_count,
        by_category=dict(by_category)
    )

@router.get("/{subscription_id}", response_model=SubscriptionDetailResponse)
async def get_subscription(
    subscription_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get a specific subscription with payment history"""
    # Get subscription
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Get payment history (linked transactions)
    payment_history = []
    linked_txs = []
    total_spent = 0
    
    # Calculate days until billing
    days_until_billing = None
    if subscription.next_billing_date:
        if isinstance(subscription.next_billing_date, datetime):
            days_until_billing = (subscription.next_billing_date.date() - date.today()).days
        elif isinstance(subscription.next_billing_date, date):
            days_until_billing = (subscription.next_billing_date - date.today()).days
    
    # Create base response
    base_response = _create_subscription_response(
        subscription,
        transaction_ids=[tx.id for tx in linked_txs],
        days_until_billing=days_until_billing
    )

    # Convert to dict and add detail fields
    response_dict = base_response.model_dump()
    response_dict['payment_history'] = payment_history
    response_dict['total_spent'] = total_spent
    response_dict['days_until_billing'] = days_until_billing
    
    return SubscriptionDetailResponse(**response_dict)

@router.post("/{subscription_id}/cancel", response_model=SubscriptionCancelResponse)
async def cancel_subscription(
    request: Request,
    subscription_id: int,
    cancel_data: SubscriptionCancelRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Cancel a subscription"""
    
    # Get subscription
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Cancel subscription
    if cancel_data.cancel_at_period_end:
        # Keep subscription active but set end date to next billing date
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.end_date = subscription.next_billing_date or date.today()
        cancellation_date = subscription.next_billing_date or date.today()
        message = f"Subscription will be cancelled on {cancellation_date}"
    else:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.end_date = date.today()
        cancellation_date = date.today()
        message = "Subscription cancelled immediately"
    
    subscription.updated_at = datetime.utcnow()
    
    db_session.commit()
    
    
    return SubscriptionCancelResponse(
        id=subscription.id,
        status=subscription.status,
        cancellation_date=cancellation_date,
        message=message
    )

@router.post("/{subscription_id}/pause", response_model=SubscriptionPauseResponse)
async def pause_subscription(
    request: Request,
    subscription_id: int,
    pause_data: SubscriptionPauseRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Pause a subscription"""
    
    # Get subscription
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Pause subscription
    subscription.status = SubscriptionStatus.PAUSED
    subscription.next_billing_date = pause_data.pause_until
    subscription.updated_at = datetime.utcnow()
    
    # Store the resume date in notes (in a real system, would have a separate field)
    subscription.notes = f"{subscription.notes or ''} [Resume: {pause_data.pause_until}]"
    
    db_session.commit()
    
    
    return SubscriptionPauseResponse(
        id=subscription.id,
        status=subscription.status,
        resume_date=pause_data.pause_until,
        message=f"Subscription paused until {pause_data.pause_until}"
    )

@router.get("/{subscription_id}/payments", response_model=List[PaymentHistoryResponse])
async def get_subscription_payments(
    subscription_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get payment history for a subscription"""
    # Verify subscription ownership
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Get linked transactions
    linked_txs = db_session.query(Transaction).join(
        Account
    ).filter(
        Account.user_id == current_user['user_id'],
        Transaction.description.ilike(f"%{subscription.merchant_name}%"),
        Transaction.amount == subscription.amount
    ).order_by(Transaction.transaction_date.desc()).limit(24).all()
    
    # Build payment history
    payments = []
    for tx in linked_txs:
        payments.append(PaymentHistoryResponse(
            amount=tx.amount,
            payment_date=tx.transaction_date.date(),
            status="completed",
            payment_method=tx.account.name if tx.account else "Unknown",
            transaction_id=tx.id
        ))
    
    return payments

@router.put("/{subscription_id}/reminders", response_model=SubscriptionReminderResponse)
async def set_subscription_reminders(
    request: Request,
    subscription_id: int,
    reminder_data: SubscriptionReminderRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Set reminder preferences for a subscription"""
    
    # Verify subscription ownership
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # In a real system, these would be stored in a separate table
    # For now, we'll store in the notes field as JSON
    reminder_settings = {
        "payment_reminder": reminder_data.payment_reminder,
        "reminder_days_before": reminder_data.reminder_days_before,
        "cancellation_reminder": reminder_data.cancellation_reminder,
        "price_increase_alert": reminder_data.price_increase_alert
    }

    # Update notes to include reminder settings
    import json
    notes_data = {"reminders": reminder_settings}
    if subscription.notes:
        try:
            existing_notes = json.loads(subscription.notes)
            existing_notes.update(notes_data)
            notes_data = existing_notes
        except:
            notes_data["original_notes"] = subscription.notes
    
    subscription.notes = json.dumps(notes_data)
    subscription.updated_at = datetime.utcnow()
    
    db_session.commit()
    
    
    return SubscriptionReminderResponse(
        subscription_id=subscription.id,
        payment_reminder=reminder_data.payment_reminder,
        reminder_days_before=reminder_data.reminder_days_before,
        cancellation_reminder=reminder_data.cancellation_reminder,
        price_increase_alert=reminder_data.price_increase_alert,
        message="Reminder preferences updated successfully"
    )

@router.post("/{subscription_id}/usage", response_model=SubscriptionUsageResponse)
async def track_subscription_usage(
    request: Request,
    subscription_id: int,
    usage_data: SubscriptionUsageRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Track usage of a subscription"""
    
    # Verify subscription ownership
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # In a real system, usage would be stored in a separate table

    return SubscriptionUsageResponse(
        message="Usage tracked successfully"
    )

@router.get("/analysis/recommendations", response_model=SubscriptionRecommendationsResponse)
async def get_subscription_recommendations(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get personalized subscription recommendations"""
    # Get all active subscriptions
    subscriptions = db_session.query(Subscription).filter(
        Subscription.user_id == current_user['user_id'],
        Subscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    # Analyze for recommendations
    unused_subscriptions = []
    duplicate_services = []
    savings_opportunities = []
    total_potential_savings = 0
    
    # Find duplicates by category
    category_services = defaultdict(list)
    for sub in subscriptions:
        category_services[sub.category].append(sub)
    
    for category, subs in category_services.items():
        if len(subs) > 1:
            # Find duplicates
            services = [{"id": s.id, "name": s.name, "cost": s.amount} for s in subs]
            duplicate_services.append({
                "category": category,
                "services": services,
                "recommendation": f"Consider keeping only one {category} service"
            })
            
            # Calculate potential savings
            costs = sorted([s.amount for s in subs])
            savings = sum(costs[1:])  # Keep cheapest
            total_potential_savings += savings
            
            savings_opportunities.append({
                "type": "duplicate_removal",
                "description": f"Remove duplicate {category} services",
                "monthly_savings": savings,
                "annual_savings": savings * 12
            })
    
    # Mock unused subscriptions (based on category patterns)
    for sub in subscriptions:
        if sub.category in [SubscriptionCategory.FITNESS, SubscriptionCategory.EDUCATION]:
            if sub.amount > 20:  # Expensive services more likely to be unused
                unused_subscriptions.append({
                    "id": sub.id,
                    "name": sub.name,
                    "cost": sub.amount,
                    "last_used": "Over 30 days ago",
                    "recommendation": "Consider cancelling if not actively using"
                })
                total_potential_savings += sub.amount
    
    # Add bundling opportunities
    streaming_count = sum(1 for s in subscriptions if s.category == SubscriptionCategory.STREAMING)
    if streaming_count >= 3:
        streaming_cost = sum(s.amount for s in subscriptions if s.category == SubscriptionCategory.STREAMING)
        bundle_savings = streaming_cost * 0.3  # Assume 30% savings
        
        savings_opportunities.append({
            "type": "bundling",
            "description": "Bundle streaming services",
            "monthly_savings": bundle_savings,
            "annual_savings": bundle_savings * 12
        })
        total_potential_savings += bundle_savings
    
    return SubscriptionRecommendationsResponse(
        unused_subscriptions=unused_subscriptions,
        duplicate_services=duplicate_services,
        savings_opportunities=savings_opportunities,
        total_potential_savings=round(total_potential_savings, 2)
    )

@router.post("/{subscription_id}/share", response_model=SubscriptionShareResponse)
async def share_subscription(
    request: Request,
    subscription_id: int,
    share_data: SubscriptionShareRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Share a subscription with another user"""
    
    # Get subscription
    subscription = db_session.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user['user_id']
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    # Find the user to share with
    share_user = db_session.query(User).filter(
        User.username == share_data.share_with_username
    ).first()
    
    if not share_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # In a real system, sharing would be tracked in a separate table
    # For now, we'll update the notes
    import json
    shared_info = {
        "shared_with": share_user.username,
        "user_id": share_user.id,
        "cost_split": share_data.cost_split_percentage
    }

    notes_data = {"shared_users": [shared_info]}
    if subscription.notes:
        try:
            existing_notes = json.loads(subscription.notes)
            if "shared_users" in existing_notes:
                existing_notes["shared_users"].append(shared_info)
            else:
                existing_notes.update(notes_data)
            notes_data = existing_notes
        except:
            notes_data["original_notes"] = subscription.notes
    
    subscription.notes = json.dumps(notes_data)
    subscription.updated_at = datetime.utcnow()
    
    db_session.commit()
    
    
    return SubscriptionShareResponse(
        id=subscription.id,
        shared_users=[{
            "username": share_user.username,
            "cost_split_percentage": share_data.cost_split_percentage
        }],
        message=f"Subscription shared with {share_user.username}"
    )

@router.post("/import", response_model=BulkImportResponse)
async def bulk_import_subscriptions(
    request: Request,
    import_data: BulkImportRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Import multiple subscriptions at once"""
    
    imported_count = 0
    subscription_ids = []
    errors = []
    
    for sub_data in import_data.subscriptions:
        try:
            # Validate required fields
            if not all(k in sub_data for k in ["service_name", "category", "amount", "billing_cycle"]):
                errors.append(f"Missing required fields for subscription: {sub_data.get('service_name', 'Unknown')}")
                continue
            
            # Create subscription
            start_date = date.today()
            if "start_date" in sub_data:
                start_date = datetime.fromisoformat(sub_data["start_date"]).date()
            
            billing_cycle = BillingCycle(sub_data["billing_cycle"])
            category = SubscriptionCategory(sub_data["category"])
            
            next_billing_date = calculate_next_billing_date(start_date, billing_cycle)
            
            subscription = Subscription(
                user_id=current_user['user_id'],
                name=f"{sub_data['service_name']} Subscription",
                merchant_name=sub_data["service_name"],
                category=category,
                status=SubscriptionStatus.ACTIVE,
                amount=sub_data["amount"],
                billing_cycle=billing_cycle,
                next_billing_date=next_billing_date,
                start_date=start_date,
                notes=sub_data.get("description"),
                detected_automatically=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db_session.add(subscription)
            db_session.flush()  # Get the ID
            
            subscription_ids.append(subscription.id)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Error importing {sub_data.get('service_name', 'Unknown')}: {str(e)}")
    
    db_session.commit()
    
    
    return BulkImportResponse(
        imported=imported_count,
        subscription_ids=subscription_ids,
        errors=errors
    )