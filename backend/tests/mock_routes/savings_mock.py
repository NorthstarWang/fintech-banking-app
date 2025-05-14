"""
Mock implementation for savings routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
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

@router.get("")
async def get_savings_goals(
    category: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all savings goals for user."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goals = [g for g in data_manager.savings_goals if g["user_id"] == current_user["id"]]
    
    if category:
        goals = [g for g in goals if g.get("category") == category]
    
    # Add progress percentage to each goal
    for goal in goals:
        if goal["target_amount"] > 0:
            goal["progress_percentage"] = (goal["current_amount"] / goal["target_amount"]) * 100
        else:
            goal["progress_percentage"] = 0
    
    return goals

@router.post("", status_code=200)  # Changed from 201 to 200
async def create_savings_goal(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = {
        "id": str(len(data_manager.savings_goals) + 1),
        "user_id": current_user["id"],
        "goal_name": data.get("goal_name", "Savings Goal"),  # Changed from "name"
        "target_amount": float(data.get("target_amount", 0)),
        "current_amount": float(data.get("current_amount", 0)),
        "target_date": data.get("target_date"),
        "category": data.get("category", "general"),
        "description": data.get("description", ""),
        "account_id": data.get("account_id"),
        "auto_transfer_enabled": data.get("auto_transfer_enabled", False),
        "auto_transfer_amount": float(data.get("auto_transfer_amount", 0)),
        "auto_transfer_frequency": data.get("auto_transfer_frequency", "monthly"),
        "is_shared": data.get("is_shared", False),
        "shared_with": data.get("shared_with", []),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Calculate progress percentage
    if goal["target_amount"] > 0:
        goal["progress_percentage"] = (goal["current_amount"] / goal["target_amount"]) * 100
    else:
        goal["progress_percentage"] = 0
    
    # Add days remaining if target date is set  
    if goal.get("target_date"):
        try:
            target_date = datetime.fromisoformat(goal["target_date"].replace("Z", "+00:00"))
            days_remaining = (target_date - datetime.now()).days
            goal["days_remaining"] = max(0, days_remaining)
        except:
            pass  # Skip if date parsing fails
    
    # Initialize contribution history
    if not hasattr(data_manager, 'goal_contributions'):
        data_manager.goal_contributions = []
    
    data_manager.savings_goals.append(goal)
    return goal

@router.get("/summary")
async def get_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get savings summary."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goals = [g for g in data_manager.savings_goals if g["user_id"] == current_user["id"]]
    
    active_goals = [g for g in goals if g.get("status", "active") == "active"]
    completed_goals = [g for g in goals if g.get("status", "active") == "completed"]
    
    total_target = sum(g["target_amount"] for g in goals)
    total_saved = sum(g["current_amount"] for g in goals)
    
    # Calculate average progress
    if goals:
        total_progress = sum(g.get("progress_percentage", 0) for g in goals)
        average_progress = total_progress / len(goals)
    else:
        average_progress = 0
    
    # Group goals by category
    goals_by_category = {}
    for goal in goals:
        category = goal.get("category", "general")
        if category not in goals_by_category:
            goals_by_category[category] = 0
        goals_by_category[category] += 1
    
    return {
        "total_goals": len(goals),
        "active_goals": len(active_goals),
        "completed_goals": len(completed_goals),
        "total_target": total_target,
        "total_saved": total_saved,
        "completion_percentage": (total_saved / total_target * 100) if total_target > 0 else 0,
        "average_progress": average_progress,
        "goals_by_category": goals_by_category
    }

@router.post("/shared", status_code=200)
async def create_shared_goal(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a shared savings goal."""
    # Handle shared with username
    shared_with_username = data.get("shared_with_username")
    shared_with = []
    
    if shared_with_username:
        shared_user = next((u for u in data_manager.users if u["username"] == shared_with_username), None)
        if shared_user:
            shared_with.append(shared_user["username"])
    
    data["is_shared"] = True
    data["shared_with"] = shared_with
    
    # Create the goal
    goal = await create_savings_goal(data, current_user)
    
    # Add participants list
    participants = [current_user["username"]]
    participants.extend(shared_with)
    goal["participants"] = participants
    
    return goal

@router.get("/{goal_id}")
async def get_savings_goal(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get specific savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and 
                (g["user_id"] == current_user["id"] or current_user["username"] in g.get("shared_with", []))), 
               None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    # Add progress percentage
    if goal["target_amount"] > 0:
        goal["progress_percentage"] = (goal["current_amount"] / goal["target_amount"]) * 100
    else:
        goal["progress_percentage"] = 0
    
    # Add days remaining
    if goal.get("target_date"):
        try:
            target_date = datetime.fromisoformat(goal["target_date"].replace("Z", "+00:00"))
            days_remaining = (target_date - datetime.now()).days
            goal["days_remaining"] = max(0, days_remaining)
        except:
            goal["days_remaining"] = None
    else:
        goal["days_remaining"] = None
    
    # Calculate monthly contribution needed
    remaining_amount = goal["target_amount"] - goal["current_amount"]
    if goal.get("target_date") and remaining_amount > 0:
        try:
            target_date = datetime.fromisoformat(goal["target_date"].replace("Z", "+00:00"))
            months_remaining = max(1, (target_date.year - datetime.now().year) * 12 + 
                                  (target_date.month - datetime.now().month))
            goal["monthly_contribution_needed"] = remaining_amount / months_remaining
        except:
            goal["monthly_contribution_needed"] = 0
    else:
        goal["monthly_contribution_needed"] = 0
    
    return goal

@router.put("/{goal_id}")
async def update_savings_goal(goal_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Update savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    # Update fields
    for key, value in data.items():
        if key in ["goal_name", "target_amount", "target_date", "description", 
                   "auto_transfer_enabled", "auto_transfer_amount", "auto_transfer_frequency"]:
            goal[key] = value
    
    goal["updated_at"] = datetime.utcnow().isoformat()
    
    # Recalculate progress
    if goal["target_amount"] > 0:
        goal["progress_percentage"] = (goal["current_amount"] / goal["target_amount"]) * 100
    else:
        goal["progress_percentage"] = 0
    
    return goal

@router.delete("/{goal_id}")
async def delete_savings_goal(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    data_manager.savings_goals.remove(goal)
    return {"message": "Savings goal deleted successfully"}

@router.post("/{goal_id}/contribute", status_code=200)
async def add_contribution(
    goal_id: str, 
    data: Dict[str, Any], 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add contribution to savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    if not hasattr(data_manager, 'goal_contributions'):
        data_manager.goal_contributions = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    amount = float(data.get("amount", 0))
    account_id = data.get("account_id")
    
    # Deduct from account if specified
    if account_id:
        account = next((a for a in data_manager.accounts 
                       if str(a["id"]) == str(account_id) and a["user_id"] == current_user["id"]), None)
        if account and account["balance"] >= amount:
            account["balance"] -= amount
        elif account:
            raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Add to goal
    goal["current_amount"] = goal.get("current_amount", 0) + amount
    goal["updated_at"] = datetime.utcnow().isoformat()
    
    # Recalculate progress
    if goal["target_amount"] > 0:
        goal["progress_percentage"] = (goal["current_amount"] / goal["target_amount"]) * 100
    else:
        goal["progress_percentage"] = 0
    
    # Record contribution
    contribution = {
        "id": str(len(data_manager.goal_contributions) + 1),
        "goal_id": goal_id,
        "user_id": current_user["id"],
        "amount": amount,
        "type": "contribution",
        "contribution_date": datetime.utcnow().isoformat(),
        "account_id": account_id,
        "balance_after": goal["current_amount"]
    }
    data_manager.goal_contributions.append(contribution)
    
    # Check if goal is completed
    goal_completed = goal["progress_percentage"] >= 100
    
    result = {
        "message": "Contribution added successfully",
        "contribution_amount": amount,
        "new_balance": goal["current_amount"],
        "new_progress_percentage": goal["progress_percentage"],
        "progress_percentage": goal["progress_percentage"],
        "transaction_id": contribution["id"]
    }
    
    if goal_completed:
        result["goal_completed"] = True
    
    return result

@router.post("/{goal_id}/withdraw", status_code=200)
async def withdraw_from_goal(
    goal_id: str, 
    data: Dict[str, Any], 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Withdraw from savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    amount = float(data.get("amount", 0))
    
    if goal["current_amount"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in goal")
    
    # Withdraw from goal
    goal["current_amount"] -= amount
    goal["updated_at"] = datetime.utcnow().isoformat()
    
    # Recalculate progress
    if goal["target_amount"] > 0:
        goal["progress_percentage"] = (goal["current_amount"] / goal["target_amount"]) * 100
    else:
        goal["progress_percentage"] = 0
    
    # Add to account if specified
    account_id = data.get("to_account_id") or data.get("account_id")
    if account_id:
        account = next((a for a in data_manager.accounts 
                       if str(a["id"]) == str(account_id) and a["user_id"] == current_user["id"]), None)
        if account:
            account["balance"] += amount
    
    # Record withdrawal in contribution history
    if not hasattr(data_manager, 'goal_contributions'):
        data_manager.goal_contributions = []
    
    withdrawal = {
        "id": str(len(data_manager.goal_contributions) + 1),
        "goal_id": goal_id,
        "user_id": current_user["id"],
        "amount": -amount,  # Negative for withdrawal
        "type": "withdrawal",
        "contribution_date": datetime.utcnow().isoformat(),
        "account_id": account_id,
        "reason": data.get("reason", ""),
        "balance_after": goal["current_amount"]
    }
    data_manager.goal_contributions.append(withdrawal)
    
    return {
        "message": "Withdrawal successful",
        "withdrawal_amount": amount,
        "new_balance": goal["current_amount"],
        "new_progress_percentage": goal["progress_percentage"],
        "progress_percentage": goal["progress_percentage"]
    }

@router.get("/{goal_id}/history")
async def get_contribution_history(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get contribution history for a goal."""
    if not hasattr(data_manager, 'goal_contributions'):
        data_manager.goal_contributions = []
    
    # Verify goal exists and user has access
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    contributions = [c for c in data_manager.goal_contributions if c["goal_id"] == goal_id]
    
    # Add date field as alias for contribution_date
    for contrib in contributions:
        contrib["date"] = contrib.get("contribution_date")
    
    return contributions

@router.get("/{goal_id}/projections")
async def get_projections(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get savings projections."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    remaining_amount = goal["target_amount"] - goal["current_amount"]
    
    # Calculate months until target date
    if goal.get("target_date"):
        target_date = datetime.fromisoformat(goal["target_date"].replace("Z", "+00:00"))
        months_remaining = max(1, (target_date.year - datetime.now().year) * 12 + 
                              (target_date.month - datetime.now().month))
    else:
        months_remaining = 12  # Default to 1 year
    
    monthly_needed = remaining_amount / months_remaining if months_remaining > 0 else 0
    
    weekly_needed = monthly_needed / 4.33  # Average weeks per month
    
    # Check if on track
    on_track = goal.get("auto_transfer_enabled", False) and goal.get("auto_transfer_amount", 0) >= monthly_needed
    
    # Create scenarios
    scenarios = [
        {
            "name": "Conservative",
            "monthly_contribution": monthly_needed * 1.2,
            "projected_completion_months": int(remaining_amount / (monthly_needed * 1.2)) if monthly_needed > 0 else 999
        },
        {
            "name": "Moderate", 
            "monthly_contribution": monthly_needed,
            "projected_completion_months": months_remaining
        },
        {
            "name": "Aggressive",
            "monthly_contribution": monthly_needed * 0.8,
            "projected_completion_months": int(remaining_amount / (monthly_needed * 0.8)) if monthly_needed > 0 else 999
        }
    ]
    
    return {
        "projected_completion": goal.get("target_date", "2025-12-31"),
        "projected_completion_date": goal.get("target_date", "2025-12-31"),  # Alias
        "monthly_requirement": monthly_needed,
        "monthly_contribution_needed": monthly_needed,  # Alias for test compatibility
        "weekly_contribution_needed": weekly_needed,
        "remaining_amount": remaining_amount,
        "months_remaining": months_remaining,
        "on_track": on_track,
        "scenarios": scenarios
    }

@router.put("/{goal_id}/auto-transfer", status_code=200)
async def setup_auto_transfer(
    goal_id: str,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Setup automated transfer for savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    goal["auto_transfer_enabled"] = data.get("enabled", True)
    goal["auto_transfer_amount"] = float(data.get("amount", 0))
    goal["auto_transfer_frequency"] = data.get("frequency", "monthly")
    goal["auto_transfer_day"] = data.get("day_of_month", 1)
    goal["auto_transfer_account_id"] = data.get("from_account_id") or data.get("account_id")
    goal["auto_transfer_start_date"] = data.get("start_date")
    goal["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "message": "Automated transfer set up successfully",
        "auto_transfer_enabled": goal["auto_transfer_enabled"],
        "auto_transfer_amount": goal["auto_transfer_amount"],
        "auto_transfer_frequency": goal["auto_transfer_frequency"],
        "transfer_amount": goal["auto_transfer_amount"],
        "frequency": goal["auto_transfer_frequency"]
    }

@router.get("/{goal_id}/milestones")
async def get_milestones(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get goal milestones."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    progress = goal.get("progress_percentage", 0)
    
    milestones = [
        {"percentage": 25, "reached": progress >= 25, "reached_at": datetime.utcnow().isoformat() if progress >= 25 else None},
        {"percentage": 50, "reached": progress >= 50, "reached_at": datetime.utcnow().isoformat() if progress >= 50 else None},
        {"percentage": 75, "reached": progress >= 75, "reached_at": datetime.utcnow().isoformat() if progress >= 75 else None},
        {"percentage": 100, "reached": progress >= 100, "reached_at": datetime.utcnow().isoformat() if progress >= 100 else None}
    ]
    
    return milestones

@router.post("/{goal_id}/complete", status_code=200)
async def complete_goal(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Mark goal as completed."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals 
                if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    goal["status"] = "completed"
    goal["completed_at"] = datetime.utcnow().isoformat()
    goal["updated_at"] = datetime.utcnow().isoformat()
    
    # Return the updated goal with completion status
    goal_copy = goal.copy()
    goal_copy["goal_completed"] = True
    return goal_copy

@router.get("/{goal_id}/permissions")
async def get_permissions(goal_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get permissions for savings goal."""
    if not hasattr(data_manager, 'savings_goals'):
        data_manager.savings_goals = []
    
    goal = next((g for g in data_manager.savings_goals if g["id"] == goal_id), None)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    
    permissions = []
    if goal["user_id"] == current_user["id"]:
        permissions = ["view", "edit", "delete", "contribute", "withdraw"]
    elif current_user["username"] in goal.get("shared_with", []):
        permissions = ["view", "contribute"]
    
    return {"permissions": permissions}