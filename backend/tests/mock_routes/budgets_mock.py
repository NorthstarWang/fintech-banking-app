"""
Mock implementation for budgets routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, date
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
async def get_budgets(
    period: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all budgets for user."""
    user_budgets = [
        b for b in data_manager.budgets 
        if b["user_id"] == current_user["id"]
    ]
    
    if period:
        user_budgets = [b for b in user_budgets if b.get("period") == period]
    
    return user_budgets

@router.post("", status_code=201)
async def create_budget(
    data: Dict[str, Any], 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new budget."""
    # Validate category exists
    category_id = data.get("category_id")
    if category_id:
        category = next(
            (c for c in data_manager.categories if str(c["id"]) == str(category_id)),
            None
        )
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")
    
    budget = {
        "id": str(len(data_manager.budgets) + 1),
        "user_id": current_user["id"],
        "name": data.get("name", "Budget"),
        "amount": float(data.get("amount", 0)),
        "spent_amount": 0.0,  # Track spending against budget
        "period": data.get("period", "monthly"),
        "category_id": category_id,
        "start_date": data.get("start_date", date.today().isoformat()),
        "end_date": data.get("end_date"),
        "is_active": True,
        "rollover_enabled": data.get("rollover_enabled", False),
        "rollover_amount": 0.0,  # Amount rolled over from previous period
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    data_manager.budgets.append(budget)
    
    # Return with calculated fields
    budget_response = budget.copy()
    budget_response["remaining_amount"] = budget["amount"] - budget["spent_amount"]
    
    return budget_response

@router.get("/{budget_id}")
async def get_budget(
    budget_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific budget."""
    budget = next(
        (b for b in data_manager.budgets 
         if b["id"] == budget_id and b["user_id"] == current_user["id"]), 
        None
    )
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Add calculated fields
    budget_copy = budget.copy()
    spent = budget.get("spent_amount", 0)
    budget_copy["remaining_amount"] = budget["amount"] - spent
    budget_copy["percentage_used"] = (spent / budget["amount"] * 100) if budget["amount"] > 0 else 0
    
    return budget_copy

@router.put("/{budget_id}")
async def update_budget(
    budget_id: str, 
    data: Dict[str, Any], 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update budget."""
    budget = next(
        (b for b in data_manager.budgets 
         if b["id"] == budget_id and b["user_id"] == current_user["id"]), 
        None
    )
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Update fields
    if "name" in data:
        budget["name"] = data["name"]
    if "amount" in data:
        budget["amount"] = float(data["amount"])
    if "period" in data:
        budget["period"] = data["period"]
    if "is_active" in data:
        budget["is_active"] = data["is_active"]
    
    budget["updated_at"] = datetime.utcnow().isoformat()
    return budget

@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete budget."""
    budget = next(
        (b for b in data_manager.budgets 
         if b["id"] == budget_id and b["user_id"] == current_user["id"]), 
        None
    )
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    data_manager.budgets.remove(budget)
    return {"message": "Budget deleted successfully"}

@router.get("/{budget_id}/alerts")
async def get_budget_alerts(
    budget_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get alerts for a budget."""
    budget = next(
        (b for b in data_manager.budgets 
         if b["id"] == budget_id and b["user_id"] == current_user["id"]), 
        None
    )
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Return mock alerts
    return [{
        "id": "1",
        "budget_id": budget_id,
        "type": "threshold",
        "threshold_percentage": 80,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }]

@router.post("/{budget_id}/rollover", status_code=200)
async def rollover_budget(
    budget_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Rollover budget to next period."""
    budget = next(
        (b for b in data_manager.budgets 
         if b["id"] == budget_id and b["user_id"] == current_user["id"]), 
        None
    )
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Create new budget for next period
    new_budget = budget.copy()
    new_budget["id"] = str(len(data_manager.budgets) + 1)
    new_budget["spent_amount"] = 0.0  # Reset spending for new period
    
    # Calculate rollover amount
    remaining = budget["amount"] - budget.get("spent_amount", 0)
    if budget.get("rollover_enabled", False) and remaining > 0:
        new_budget["rollover_amount"] = remaining
        new_budget["amount"] = budget["amount"] + remaining
    else:
        new_budget["rollover_amount"] = 0.0
    
    new_budget["created_at"] = datetime.utcnow().isoformat()
    new_budget["updated_at"] = datetime.utcnow().isoformat()
    
    # Update dates based on period
    if budget["period"] == "monthly":
        # Move dates by one month (simplified)
        pass
    
    data_manager.budgets.append(new_budget)
    return new_budget

@router.get("/{budget_id}/permissions")
async def get_budget_permissions(
    budget_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get budget permissions."""
    budget = next(
        (b for b in data_manager.budgets 
         if b["id"] == budget_id and b["user_id"] == current_user["id"]), 
        None
    )
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    return {
        "budget_id": budget_id,
        "permissions": ["view", "edit", "delete"]
    }
