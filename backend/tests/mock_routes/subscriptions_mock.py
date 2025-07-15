"""
Mock implementation for subscriptions routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.repositories.data_manager import data_manager

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

def calculate_next_billing_date(start_date: str, billing_cycle: str) -> str:
    """Calculate next billing date based on billing cycle"""
    # Parse the date properly, handling Z timezone
    if 'Z' in start_date:
        start_date = start_date.replace('Z', '+00:00')
    start = datetime.fromisoformat(start_date)
    
    if billing_cycle == "monthly":
        next_date = start + timedelta(days=30)
    elif billing_cycle == "annual":
        next_date = start + timedelta(days=365)
    elif billing_cycle == "weekly":
        next_date = start + timedelta(days=7)
    elif billing_cycle == "quarterly":
        next_date = start + timedelta(days=90)
    else:
        next_date = start + timedelta(days=30)  # Default to monthly
    
    # Return with single Z timezone
    return next_date.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

@router.get("")
async def get_subscriptions(
    category: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    user_subs = [s for s in data_manager.subscriptions if s["user_id"] == current_user["id"]]
    
    if category:
        user_subs = [s for s in user_subs if s.get("category") == category]
    
    return user_subs

@router.post("", status_code=201)
async def create_subscription(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    if not hasattr(data_manager, 'subscription_counter'):
        data_manager.subscription_counter = 1
    
    # Handle start_date
    start_date = data.get("start_date", datetime.now().isoformat())
    if isinstance(start_date, str) and not start_date.endswith('Z'):
        start_date = start_date + 'Z' if 'T' in start_date else start_date + 'T00:00:00Z'
    
    subscription = {
        "id": str(data_manager.subscription_counter),
        "user_id": current_user["id"],
        "merchant_name": data.get("service_name", "Subscription"),
        "service_name": data.get("service_name", "Subscription"),
        "category": data.get("category", "other"),
        "amount": data.get("amount", 0),
        "billing_cycle": data.get("billing_cycle", "monthly"),
        "frequency": data.get("billing_cycle", "monthly"),  # For backward compatibility
        "status": "active",
        "start_date": start_date,
        "next_billing_date": calculate_next_billing_date(start_date, data.get("billing_cycle", "monthly")),
        "payment_method_id": data.get("payment_method_id"),
        "auto_renew": data.get("auto_renew", True),
        "description": data.get("description"),
        "is_trial": data.get("is_trial", False),
        "trial_end_date": data.get("trial_end_date"),
        "regular_price": data.get("regular_price", data.get("amount", 0)),
        "shareable": data.get("shareable", False),
        "max_users": data.get("max_users", 1),
        "shared_users": [],
        "created_at": datetime.utcnow().isoformat() + 'Z'
    }
    
    # Calculate days until billing for trials
    if subscription["is_trial"] and subscription["trial_end_date"]:
        trial_end = datetime.fromisoformat(subscription["trial_end_date"].replace('Z', '+00:00'))
        days_until = (trial_end - datetime.now()).days
        subscription["days_until_billing"] = days_until
    
    data_manager.subscription_counter += 1
    data_manager.subscriptions.append(subscription)
    return subscription

@router.get("/summary")
async def get_spending_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    user_subs = [s for s in data_manager.subscriptions if s["user_id"] == current_user["id"]]
    
    active_subs = [s for s in user_subs if s["status"] == "active"]
    paused_subs = [s for s in user_subs if s["status"] == "paused"]
    cancelled_subs = [s for s in user_subs if s["status"] in ["cancelled", "pending_cancellation"]]
    
    # Calculate costs
    monthly_total = 0
    for sub in active_subs:
        if sub["billing_cycle"] == "monthly":
            monthly_total += sub["amount"]
        elif sub["billing_cycle"] == "annual":
            monthly_total += sub["amount"] / 12
        elif sub["billing_cycle"] == "weekly":
            monthly_total += sub["amount"] * 4.33  # Average weeks per month
        elif sub["billing_cycle"] == "quarterly":
            monthly_total += sub["amount"] / 3
    
    # Group by category
    by_category = {}
    for sub in active_subs:
        cat = sub.get("category", "other")
        if cat not in by_category:
            by_category[cat] = {"count": 0, "monthly_cost": 0}
        by_category[cat]["count"] += 1
        
        if sub["billing_cycle"] == "monthly":
            by_category[cat]["monthly_cost"] += sub["amount"]
        elif sub["billing_cycle"] == "annual":
            by_category[cat]["monthly_cost"] += sub["amount"] / 12
        elif sub["billing_cycle"] == "weekly":
            by_category[cat]["monthly_cost"] += sub["amount"] * 4.33
        elif sub["billing_cycle"] == "quarterly":
            by_category[cat]["monthly_cost"] += sub["amount"] / 3
    
    return {
        "total_monthly_cost": round(monthly_total, 2),
        "total_annual_cost": round(monthly_total * 12, 2),
        "active_subscriptions": len(active_subs),
        "paused_subscriptions": len(paused_subs),
        "cancelled_subscriptions": len(cancelled_subs),
        "by_category": by_category
    }

@router.get("/recommendations")
async def get_recommendations(current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    user_subs = [s for s in data_manager.subscriptions if s["user_id"] == current_user["id"] and s["status"] == "active"]
    
    # Mock recommendations
    unused_subscriptions = []
    duplicate_services = []
    savings_opportunities = []
    
    # Find potential duplicates by category
    categories = {}
    for sub in user_subs:
        cat = sub.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(sub)
    
    for cat, subs in categories.items():
        if len(subs) > 1:
            duplicate_services.append({
                "category": cat,
                "subscriptions": [{"id": s["id"], "name": s["service_name"], "amount": s["amount"]} for s in subs],
                "potential_savings": sum(s["amount"] for s in subs[1:])
            })
    
    total_savings = sum(item["potential_savings"] for item in duplicate_services)
    
    return {
        "unused_subscriptions": unused_subscriptions,
        "duplicate_services": duplicate_services,
        "savings_opportunities": savings_opportunities,
        "total_potential_savings": round(total_savings, 2)
    }

@router.post("/import")
async def import_subscriptions(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    if not hasattr(data_manager, 'subscription_counter'):
        data_manager.subscription_counter = 1
    
    imported_ids = []
    subscriptions_to_import = data.get("subscriptions", [])
    
    for sub_data in subscriptions_to_import:
        # Create subscription similar to create_subscription endpoint
        start_date = sub_data.get("start_date", datetime.now().isoformat())
        if isinstance(start_date, str) and not start_date.endswith('Z'):
            start_date = start_date + 'Z' if 'T' in start_date else start_date + 'T00:00:00Z'
        
        subscription = {
            "id": str(data_manager.subscription_counter),
            "user_id": current_user["id"],
            "merchant_name": sub_data.get("service_name", "Subscription"),
            "service_name": sub_data.get("service_name", "Subscription"),
            "category": sub_data.get("category", "other"),
            "amount": sub_data.get("amount", 0),
            "billing_cycle": sub_data.get("billing_cycle", "monthly"),
            "frequency": sub_data.get("billing_cycle", "monthly"),
            "status": "active",
            "start_date": start_date,
            "next_billing_date": calculate_next_billing_date(start_date, sub_data.get("billing_cycle", "monthly")),
            "payment_method_id": sub_data.get("payment_method_id", 1),
            "auto_renew": sub_data.get("auto_renew", True),
            "description": sub_data.get("description"),
            "created_at": datetime.utcnow().isoformat() + 'Z'
        }
        
        data_manager.subscription_counter += 1
        data_manager.subscriptions.append(subscription)
        imported_ids.append(subscription["id"])
    
    return {
        "imported": len(imported_ids),
        "subscription_ids": imported_ids,
        "message": f"Successfully imported {len(imported_ids)} subscriptions"
    }

# Legacy endpoints for backward compatibility
@router.get("/spending-summary")
async def get_spending_summary_legacy(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Legacy endpoint - redirects to /summary"""
    return await get_spending_summary(current_user)

@router.get("/shared")
async def get_shared_subscriptions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get subscriptions shared with the current user"""
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    # Find subscriptions where current user is in shared_users
    shared_subs = []
    for sub in data_manager.subscriptions:
        for shared_user in sub.get("shared_users", []):
            if shared_user.get("username") == current_user.get("username"):
                shared_subs.append(sub)
                break
    
    return shared_subs

@router.get("/trials")
async def get_trials(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all trial subscriptions"""
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    trial_subs = [s for s in data_manager.subscriptions 
                  if s["user_id"] == current_user["id"] and s.get("is_trial", False)]
    
    return trial_subs

@router.get("/{subscription_id}")
async def get_subscription(subscription_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Add payment history and total spent
    sub_copy = sub.copy()
    sub_copy["payment_history"] = []
    sub_copy["total_spent"] = sub["amount"] * 3  # Mock 3 payments
    
    return sub_copy

@router.put("/{subscription_id}")
async def update_subscription(subscription_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Update allowed fields
    allowed_fields = ["amount", "description", "auto_renew", "billing_cycle", "category", "payment_method_id"]
    for field in allowed_fields:
        if field in data:
            sub[field] = data[field]
    
    # Recalculate next billing date if billing cycle changed
    if "billing_cycle" in data:
        sub["next_billing_date"] = calculate_next_billing_date(sub["start_date"], data["billing_cycle"])
    
    sub["updated_at"] = datetime.utcnow().isoformat() + 'Z'
    return sub

@router.post("/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    cancel_at_period_end = data.get("cancel_at_period_end", True)
    
    if cancel_at_period_end:
        sub["status"] = "pending_cancellation"
        sub["cancellation_date"] = sub["next_billing_date"]
    else:
        sub["status"] = "cancelled"
        sub["cancellation_date"] = datetime.utcnow().isoformat() + 'Z'
    
    return sub

@router.post("/{subscription_id}/pause")
async def pause_subscription(subscription_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    sub["status"] = "paused"
    pause_until = data.get("pause_until")
    if pause_until:
        sub["resume_date"] = pause_until
    else:
        # Default pause for 30 days
        sub["resume_date"] = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'
    
    sub["paused_at"] = datetime.utcnow().isoformat() + 'Z'
    return sub

@router.get("/{subscription_id}/payments")
async def get_payment_history(subscription_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Mock payment history
    payments = []
    for i in range(3):  # Last 3 payments
        payment_date = datetime.now() - timedelta(days=30 * (i + 1))
        payments.append({
            "id": f"payment_{subscription_id}_{i}",
            "amount": sub["amount"],
            "payment_date": payment_date.isoformat() + 'Z',
            "status": "completed",
            "payment_method": {
                "type": "card",
                "last4": "1234",
                "brand": "Visa"
            }
        })
    
    return payments

@router.put("/{subscription_id}/reminders")
async def update_reminders(subscription_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Store reminder settings
    sub["reminders"] = {
        "payment_reminder": data.get("payment_reminder", False),
        "reminder_days_before": data.get("reminder_days_before", 3),
        "cancellation_reminder": data.get("cancellation_reminder", False),
        "price_increase_alert": data.get("price_increase_alert", False)
    }
    
    return sub["reminders"]

@router.post("/{subscription_id}/usage")
async def track_usage(subscription_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Store usage data
    if "usage_history" not in sub:
        sub["usage_history"] = []
    
    sub["usage_history"].append({
        "usage_date": data.get("usage_date"),
        "duration_minutes": data.get("duration_minutes"),
        "notes": data.get("notes"),
        "tracked_at": datetime.utcnow().isoformat() + 'Z'
    })
    
    return {"message": "Usage tracked successfully"}

@router.post("/{subscription_id}/share")
async def share_subscription(subscription_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id and s["user_id"] == current_user["id"]), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if not sub.get("shareable", False):
        raise HTTPException(status_code=400, detail="This subscription is not shareable")
    
    # Check max users limit
    if len(sub.get("shared_users", [])) >= sub.get("max_users", 1) - 1:
        raise HTTPException(status_code=400, detail="Maximum users reached for this subscription")
    
    # Add shared user
    if "shared_users" not in sub:
        sub["shared_users"] = []
    
    sub["shared_users"].append({
        "username": data.get("share_with_username"),
        "cost_split_percentage": data.get("cost_split_percentage", 0),
        "shared_at": datetime.utcnow().isoformat() + 'Z'
    })
    
    return sub

@router.get("/{subscription_id}/permissions")
async def get_permissions(subscription_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user permissions for a subscription"""
    if not hasattr(data_manager, 'subscriptions'):
        data_manager.subscriptions = []
    
    sub = next((s for s in data_manager.subscriptions if s["id"] == subscription_id), None)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Check if user owns the subscription
    if sub["user_id"] == current_user["id"]:
        return {"permissions": ["view", "edit", "cancel", "share", "delete"]}
    
    # Check if user is a shared user
    for shared_user in sub.get("shared_users", []):
        if shared_user.get("username") == current_user.get("username"):
            return {"permissions": ["view"]}
    
    # No permissions
    return {"permissions": []}