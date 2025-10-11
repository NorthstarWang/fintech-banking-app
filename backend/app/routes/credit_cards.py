"""
Credit card recommendation and application API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.credit_card_manager import CreditCardManager
from app.repositories.data_manager import data_manager
from app.utils.auth import get_current_user

router = APIRouter()

# Initialize credit card manager
card_manager = CreditCardManager(data_manager)

# Credit score and factors
@router.get("/credit-score")
async def get_credit_score(
    current_user = Depends(get_current_user)
) -> dict:
    """Get user's credit score and factors."""
    score = card_manager.get_user_credit_score(current_user["user_id"])
    factors = card_manager.get_credit_factors(current_user["user_id"])
    rating = _get_score_rating(score)

    return {
        "score": score,
        "rating": rating,
        "factors": factors,
        "credit_score": score,
        "score_range": _get_score_range(score),
        "last_updated": "2024-01-15"  # Mock date
    }

@router.put("/credit-score")
async def update_credit_score(
    score_data: dict,
    current_user = Depends(get_current_user)
) -> dict:
    """Update user's credit score (simulation)."""
    new_score = score_data.get("score")
    if not new_score or not (300 <= new_score <= 850):
        raise HTTPException(status_code=400, detail="Invalid credit score")

    # In a real app, this would update the database
    # For now, just return the new score with rating
    rating = _get_score_rating(new_score)
    factors = card_manager.get_credit_factors(current_user["user_id"])

    return {
        "score": new_score,
        "rating": rating,
        "factors": factors,
        "credit_score": new_score,
        "score_range": _get_score_range(new_score)
    }

@router.get("/credit-score/simulation")
async def simulate_credit_improvement(
    months: int = Query(6, ge=1, le=24, description="Number of months to simulate"),
    current_user = Depends(get_current_user)
) -> dict:
    """Simulate credit score improvement over time."""
    return card_manager.simulate_credit_improvement(current_user["user_id"], months)

# Card browsing and recommendations
@router.get("")
async def get_all_cards(
    category: str | None = Query(None, description="Filter by category"),
    limit: int | None = Query(None, description="Limit results"),
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Browse all available credit cards."""
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []

    # Apply filters
    if category:
        offers = [o for o in offers if o.get('category') == category]

    if limit:
        offers = offers[:limit]

    return offers

@router.get("/featured")
async def get_featured_cards(
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get featured credit cards."""
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []
    return [o for o in offers if o.get('is_featured', False)]

@router.get("/offers")
async def get_all_card_offers(
    card_type: str | None = Query(None, description="Filter by card type"),
    min_credit_score: int | None = Query(None, description="Show only cards you qualify for"),
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Browse all available credit card offers."""
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []

    # Apply filters
    if card_type:
        offers = [o for o in offers if o.get('type') == card_type]

    if min_credit_score is not None:
        user_score = card_manager.get_user_credit_score(current_user["user_id"])
        if min_credit_score > 0:
            # Show only cards user qualifies for
            offers = [o for o in offers if o.get('min_credit_score', 0) <= user_score]
        else:
            # Show all cards but indicate eligibility
            for offer in offers:
                offer['eligible'] = offer.get('min_credit_score', 0) <= user_score

    return offers

@router.get("/offers/{offer_id}")
async def get_card_offer_details(
    offer_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Get detailed information about a specific card offer."""
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []
    offer = next((o for o in offers if o.get('id') == offer_id), None)

    if not offer:
        raise HTTPException(status_code=404, detail="Card offer not found")

    # Add user-specific information
    user_score = card_manager.get_user_credit_score(current_user["user_id"])

    return {
        **offer,
        "eligible": user_score >= offer.get('min_credit_score', 0),
        "estimated_credit_limit": card_manager._estimate_credit_limit(user_score, offer),
        "approval_likelihood": _calculate_approval_likelihood(user_score, offer.get('min_credit_score', 0))
    }

@router.get("/recommendations")
async def get_card_recommendations(
    income_level: str | None = None,
    spending_categories: list[str] = Query(default=[]),
    preferred_benefits: list[str] = Query(default=[]),
    limit: int | None = None,
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get personalized credit card recommendations."""
    raw_recommendations = card_manager.get_card_recommendations(current_user["user_id"])

    # Transform to expected format
    recommendations = []
    for rec in raw_recommendations:
        match_score = rec.get('match_score', 0) / 100  # Normalize to 0-1
        card_data = {k: v for k, v in rec.items() if k not in ['match_score', 'reasons']}

        recommendations.append({
            "card": card_data,
            "match_score": match_score,
            "reasons": rec.get('reasons', []),
            "estimated_approval_odds": rec.get('approval_odds', 'medium')
        })

    if limit:
        recommendations = recommendations[:limit]

    return recommendations

@router.get("/recommendations/personalized")
async def get_personalized_recommendations(
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get highly personalized credit card recommendations."""
    raw_recommendations = card_manager.get_card_recommendations(current_user["user_id"])

    # Transform to expected format
    recommendations = []
    for rec in raw_recommendations:
        match_score = rec.get('match_score', 0) / 100  # Normalize to 0-1
        card_data = {k: v for k, v in rec.items() if k not in ['match_score', 'reasons']}

        recommendations.append({
            "card": card_data,
            "match_score": match_score,
            "reasons": rec.get('reasons', []),
            "estimated_approval_odds": rec.get('approval_odds', 'medium')
        })

    return recommendations

# Applications
@router.post("/applications")
async def submit_application(
    application_data: dict,
    current_user = Depends(get_current_user)
) -> dict:
    """Submit a credit card application."""
    try:
        card_id = application_data.get("card_id")
        annual_income = application_data.get("annual_income")
        employment_type = application_data.get("employment_type")
        employment_duration_months = application_data.get("employment_duration_months")
        housing_payment = application_data.get("housing_payment")
        existing_cards_count = application_data.get("existing_cards_count")
        requested_credit_limit = application_data.get("requested_credit_limit")

        return card_manager.apply_for_card(
            current_user["user_id"],
            card_id,
            requested_credit_limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

@router.post("/apply")
async def apply_for_card(
    card_offer_id: int,
    requested_credit_limit: float | None = None,
    current_user = Depends(get_current_user)
) -> dict:
    """Apply for a credit card."""
    try:
        return card_manager.apply_for_card(
            current_user["user_id"],
            card_offer_id,
            requested_credit_limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

@router.get("/applications/stats")
async def get_application_stats(
    current_user = Depends(get_current_user)
) -> dict:
    """Get credit card application statistics."""
    applications = card_manager.get_user_applications(current_user["user_id"])

    total = len(applications)
    approved = len([a for a in applications if a.get('status') == 'approved'])
    rejected = len([a for a in applications if a.get('status') == 'rejected'])
    pending = len([a for a in applications if a.get('status') == 'pending'])

    approval_rate = approved / total if total > 0 else 0

    # Calculate average credit limit from approved applications
    approved_apps = [a for a in applications if a.get('status') == 'approved' and a.get('approved_limit')]
    avg_credit_limit = sum(a.get('approved_limit', 0) for a in approved_apps) / len(approved_apps) if approved_apps else 0

    # Get popular categories
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []
    category_counts = {}
    for app in applications:
        card = next((o for o in offers if o.get('id') == app.get('card_id')), None)
        if card and card.get('category'):
            category = card.get('category')
            category_counts[category] = category_counts.get(category, 0) + 1

    popular_categories = [{"category": k, "count": v} for k, v in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]

    return {
        "total_applications": total,
        "approved_count": approved,
        "rejected_count": rejected,
        "pending_count": pending,
        "approval_rate": approval_rate,
        "average_credit_limit": avg_credit_limit,
        "popular_categories": popular_categories
    }

@router.get("/applications")
async def get_my_applications(
    status: str | None = None,
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get user's credit card applications."""
    applications = card_manager.get_user_applications(current_user["user_id"])

    if status:
        applications = [a for a in applications if a.get('status') == status]

    return applications

@router.get("/applications/{application_id}")
async def get_application_details(
    application_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Get details of a specific application."""
    applications = card_manager.get_user_applications(current_user["user_id"])
    application = next((a for a in applications if a.get('id') == application_id), None)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return application

@router.put("/applications/{application_id}/withdraw")
async def withdraw_application(
    application_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Withdraw a credit card application."""
    applications = card_manager.get_user_applications(current_user["user_id"])
    application = next((a for a in applications if a.get('id') == application_id), None)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update status to withdrawn
    application['status'] = 'withdrawn'
    return application

# My cards
@router.get("/my-cards")
async def get_my_credit_cards(
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get user's active credit cards."""
    user_cards = [c for c in data_manager.cards
                 if c['user_id'] == current_user["user_id"] and c['card_type'] == 'credit']

    # Enhance with offer details
    enhanced_cards = []
    for card in user_cards:
        offer = next((o for o in data_manager.card_offers
                     if o['name'] == card.get('card_name')), None)

        enhanced_cards.append({
            **card,
            'benefits': offer['benefits'] if offer else [],
            'rewards_earned': _calculate_rewards(card),
            'payment_due_date': _get_payment_due_date(card),
            'minimum_payment': _calculate_minimum_payment(card)
        })

    return enhanced_cards

# Educational content
@router.get("/education/credit-basics")
async def get_credit_education(
    current_user = Depends(get_current_user)
) -> dict:
    """Get educational content about credit cards and credit scores."""
    return {
        "credit_score_factors": {
            "payment_history": {
                "weight": "35%",
                "description": "Your track record of paying bills on time",
                "tips": [
                    "Set up automatic payments",
                    "Pay at least the minimum by the due date",
                    "Contact lenders if you'll be late"
                ]
            },
            "credit_utilization": {
                "weight": "30%",
                "description": "How much credit you use compared to your limits",
                "tips": [
                    "Keep utilization below 30%",
                    "Pay down balances before statement closes",
                    "Request credit limit increases"
                ]
            },
            "credit_age": {
                "weight": "15%",
                "description": "How long you've had credit accounts",
                "tips": [
                    "Keep old accounts open",
                    "Become an authorized user on an old account",
                    "Start building credit early"
                ]
            },
            "credit_mix": {
                "weight": "10%",
                "description": "Variety of credit types (cards, loans, etc.)",
                "tips": [
                    "Have both revolving and installment credit",
                    "Don't open accounts just for mix",
                    "Focus on responsible use"
                ]
            },
            "new_credit": {
                "weight": "10%",
                "description": "Recent credit inquiries and new accounts",
                "tips": [
                    "Limit applications to when needed",
                    "Rate shop within 14-45 days",
                    "Space out applications"
                ]
            }
        },
        "card_types": {
            "cashback": "Earn a percentage back on purchases",
            "travel": "Earn points/miles for travel redemptions",
            "rewards": "Flexible points for various redemptions",
            "secured": "Requires deposit, helps build credit",
            "student": "Designed for students with limited credit",
            "business": "For business expenses and rewards",
            "balance_transfer": "Low/0% APR for transferring debt"
        },
        "glossary": {
            "APR": "Annual Percentage Rate - the yearly interest rate",
            "Credit Limit": "Maximum amount you can charge",
            "Grace Period": "Time to pay without interest (usually 21-25 days)",
            "Annual Fee": "Yearly cost to have the card",
            "Balance Transfer": "Moving debt from one card to another",
            "Cash Advance": "Withdrawing cash with your credit card (high fees!)",
            "Minimum Payment": "Least amount due to avoid late fees"
        }
    }

# Eligibility check
@router.post("/{card_id}/check-eligibility")
async def check_eligibility(
    card_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Check eligibility for a specific credit card."""
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []
    card = next((o for o in offers if o.get('id') == card_id), None)

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    user_score = card_manager.get_user_credit_score(current_user["user_id"])
    min_score = card.get('min_credit_score', 0)

    eligible = user_score >= min_score
    score_diff = user_score - min_score

    if score_diff >= 50:
        approval_odds = "high"
        reasons = ["Excellent credit score match", "Strong financial profile"]
    elif score_diff >= 0:
        approval_odds = "medium"
        reasons = ["Credit score meets minimum requirements"]
    else:
        approval_odds = "low"
        reasons = ["Credit score below minimum requirement"]

    return {
        "eligible": eligible,
        "approval_odds": approval_odds,
        "reasons": reasons
    }

# Comparison tools
@router.post("/compare")
async def compare_cards(
    comparison_data: dict,
    current_user = Depends(get_current_user)
) -> dict:
    """Compare multiple credit cards side by side."""
    card_ids = comparison_data.get("card_ids", [])

    if len(card_ids) > 5:
        raise HTTPException(status_code=400, detail="Can compare up to 5 cards at once")

    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []
    cards = []
    for card_id in card_ids:
        offer = next((o for o in offers if o.get('id') == card_id), None)
        if offer:
            cards.append(offer)

    if not cards:
        raise HTTPException(status_code=404, detail="No valid cards found")

    # Create comparison matrix
    comparison_matrix = [
        {
            "feature": "Annual Fee",
            "values": [c.get('annual_fee', 0) for c in cards]
        },
        {
            "feature": "APR Range",
            "values": [c.get('apr_range', 'N/A') for c in cards]
        },
        {
            "feature": "Min Credit Score",
            "values": [c.get('min_credit_score', 0) for c in cards]
        }
    ]

    return {
        "cards": cards,
        "comparison_matrix": comparison_matrix,
        "features": {
            "annual_fee": [c.get('annual_fee', 0) for c in cards],
            "apr_range": [c.get('apr_range', 'N/A') for c in cards],
            "min_credit_score": [c.get('min_credit_score', 0) for c in cards],
            "signup_bonus": [c.get('signup_bonus', 0) for c in cards],
            "rewards_rate": [c.get('cashback_rate', c.get('points_multiplier', 0)) for c in cards]
        },
        "best_for": {
            "no_fee": min(cards, key=lambda x: x.get('annual_fee', 0)).get('name', 'Unknown'),
            "rewards": max(cards, key=lambda x: x.get('cashback_rate', x.get('points_multiplier', 0))).get('name', 'Unknown'),
            "low_credit": min(cards, key=lambda x: x.get('min_credit_score', 999)).get('name', 'Unknown')
        }
    }

# This route MUST be last because {card_id} will match any path
@router.get("/{card_id}")
async def get_card_by_id(
    card_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Get a specific credit card by ID."""
    offers = data_manager.card_offers if hasattr(data_manager, 'card_offers') else []
    card = next((o for o in offers if o.get('id') == card_id), None)

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card


# Helper functions
def _get_score_range(score: int) -> str:
    """Get credit score range description."""
    if score >= 800:
        return "Excellent"
    if score >= 740:
        return "Very Good"
    if score >= 670:
        return "Good"
    if score >= 580:
        return "Fair"
    return "Poor"

def _get_score_rating(score: int) -> str:
    """Get credit score rating."""
    if score >= 800:
        return "excellent"
    if score >= 740:
        return "very_good"
    if score >= 670:
        return "good"
    if score >= 580:
        return "fair"
    return "poor"

def _calculate_approval_likelihood(user_score: int, min_score: int) -> str:
    """Calculate approval likelihood."""
    diff = user_score - min_score
    if diff >= 100:
        return "Very High"
    if diff >= 50:
        return "High"
    if diff >= 20:
        return "Good"
    if diff >= 0:
        return "Fair"
    return "Low"

def _calculate_rewards(card: dict) -> float:
    """Calculate rewards earned (mock)."""
    balance = card.get('current_balance', 0)
    rate = 0.02  # Assume 2% cashback
    return round(balance * rate, 2)

def _get_payment_due_date(card: dict) -> str:
    """Get payment due date (mock)."""
    from datetime import datetime, timedelta
    # Assume 25 days from now
    due_date = datetime.utcnow() + timedelta(days=25)
    return due_date.strftime("%Y-%m-%d")

def _calculate_minimum_payment(card: dict) -> float:
    """Calculate minimum payment."""
    balance = card.get('current_balance', 0)
    if balance == 0:
        return 0
    # Greater of $25 or 2% of balance
    return max(25, balance * 0.02)
