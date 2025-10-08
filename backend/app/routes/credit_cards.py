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

    return {
        "credit_score": score,
        "score_range": _get_score_range(score),
        "factors": factors,
        "last_updated": "2024-01-15"  # Mock date
    }

@router.get("/credit-score/simulation")
async def simulate_credit_improvement(
    months: int = Query(6, ge=1, le=24, description="Number of months to simulate"),
    current_user = Depends(get_current_user)
) -> dict:
    """Simulate credit score improvement over time."""
    return card_manager.simulate_credit_improvement(current_user["user_id"], months)

# Card browsing and recommendations
@router.get("/offers")
async def get_all_card_offers(
    card_type: str | None = Query(None, description="Filter by card type"),
    min_credit_score: int | None = Query(None, description="Show only cards you qualify for"),
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Browse all available credit card offers."""
    offers = data_manager.card_offers

    # Apply filters
    if card_type:
        offers = [o for o in offers if o['type'] == card_type]

    if min_credit_score is not None:
        user_score = card_manager.get_user_credit_score(current_user["user_id"])
        if min_credit_score > 0:
            # Show only cards user qualifies for
            offers = [o for o in offers if o['min_credit_score'] <= user_score]
        else:
            # Show all cards but indicate eligibility
            for offer in offers:
                offer['eligible'] = offer['min_credit_score'] <= user_score

    return offers

@router.get("/offers/{offer_id}")
async def get_card_offer_details(
    offer_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Get detailed information about a specific card offer."""
    offer = next((o for o in data_manager.card_offers if o['id'] == offer_id), None)

    if not offer:
        raise HTTPException(status_code=404, detail="Card offer not found")

    # Add user-specific information
    user_score = card_manager.get_user_credit_score(current_user["user_id"])

    return {
        **offer,
        "eligible": user_score >= offer['min_credit_score'],
        "estimated_credit_limit": card_manager._estimate_credit_limit(user_score, offer),
        "approval_likelihood": _calculate_approval_likelihood(user_score, offer['min_credit_score'])
    }

@router.get("/recommendations")
async def get_card_recommendations(
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get personalized credit card recommendations."""
    return card_manager.get_card_recommendations(current_user["user_id"])

# Applications
@router.post("/apply")
async def apply_for_card(
    card_offer_id: int,
    requested_credit_limit: float | None = None,
    current_user = Depends(get_current_user)
) -> dict:
    """Apply for a credit card."""
    try:
        result = card_manager.apply_for_card(
            current_user["user_id"],
            card_offer_id,
            requested_credit_limit
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/applications")
async def get_my_applications(
    status: str | None = Query(None, description="Filter by status"),
    current_user = Depends(get_current_user)
) -> list[dict]:
    """Get user's credit card applications."""
    applications = card_manager.get_user_applications(current_user["user_id"])

    if status:
        applications = [a for a in applications if a['status'] == status]

    return applications

@router.get("/applications/{application_id}")
async def get_application_details(
    application_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Get details of a specific application."""
    applications = card_manager.get_user_applications(current_user["user_id"])
    application = next((a for a in applications if a['id'] == application_id), None)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

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

# Comparison tools
@router.post("/compare")
async def compare_cards(
    card_ids: list[int],
    current_user = Depends(get_current_user)
) -> dict:
    """Compare multiple credit cards side by side."""
    if len(card_ids) > 5:
        raise HTTPException(status_code=400, detail="Can compare up to 5 cards at once")

    cards = []
    for card_id in card_ids:
        offer = next((o for o in data_manager.card_offers if o['id'] == card_id), None)
        if offer:
            cards.append(offer)

    if not cards:
        raise HTTPException(status_code=404, detail="No valid cards found")

    # Create comparison matrix
    comparison = {
        "cards": cards,
        "features": {
            "annual_fee": [c['annual_fee'] for c in cards],
            "apr_range": [c['apr_range'] for c in cards],
            "min_credit_score": [c['min_credit_score'] for c in cards],
            "signup_bonus": [c.get('signup_bonus', 0) for c in cards],
            "rewards_rate": [c.get('cashback_rate', c.get('points_multiplier', 0)) for c in cards]
        },
        "best_for": {
            "no_fee": min(cards, key=lambda x: x['annual_fee'])['name'],
            "rewards": max(cards, key=lambda x: x.get('cashback_rate', x.get('points_multiplier', 0)))['name'],
            "low_credit": min(cards, key=lambda x: x['min_credit_score'])['name']
        }
    }

    return comparison

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
