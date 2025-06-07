"""
Complete mock implementation for users routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.repositories.data_manager import data_manager

router = APIRouter()

class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Get current user from auth header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

@router.get("/me")
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "first_name": current_user.get("first_name", ""),
        "last_name": current_user.get("last_name", ""),
        "phone": current_user.get("phone", ""),
        "is_active": current_user.get("is_active", True),
        "is_admin": current_user.get("is_admin", False),
        "created_at": current_user.get("created_at")
    }

@router.put("/me")
async def update_current_user(
    request: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update current user profile."""
    # Find the actual user object in data_manager
    user_index = None
    for i, u in enumerate(data_manager.users):
        if u["id"] == current_user["id"]:
            user_index = i
            break
    
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the actual user object
    user = data_manager.users[user_index]
    
    # Update fields
    if request.first_name is not None:
        user["first_name"] = request.first_name
    if request.last_name is not None:
        user["last_name"] = request.last_name
    
    # Update full_name to match
    user["full_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    
    if request.email is not None:
        existing = next(
            (u for u in data_manager.users 
             if u["email"] == request.email and u["id"] != user["id"]),
            None
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user["email"] = request.email
    
    if request.phone is not None:
        user["phone"] = request.phone
    
    user["updated_at"] = datetime.utcnow().isoformat()
    
    # Update the user in the list
    data_manager.users[user_index] = user
    
    # Return updated user with first_name, last_name, and phone
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "phone": user.get("phone", ""),
        "is_active": user.get("is_active", True),
        "is_admin": user.get("is_admin", False),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at")
    }

@router.post("/me/change-password")
async def change_password(
    current_password: str = Query(...),
    new_password: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Change password."""
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Missing password fields")
    
    try:
        success = data_manager.auth_service.change_password(
            current_user["id"],
            current_password,
            new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to change password")
            
    except ValueError as e:
        if "Incorrect password" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me/preferences")
async def get_preferences(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user preferences."""
    return {
        "theme": "light",
        "notifications": True,
        "language": "en",
        "currency": "USD"
    }

@router.put("/me/preferences")
async def update_preferences(
    preferences: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user preferences."""
    return preferences

@router.get("/me/security")
async def get_security_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get security settings."""
    return {
        "two_factor_enabled": False,
        "last_login": datetime.utcnow().isoformat(),
        "active_sessions": 1
    }

@router.get("/me/activity")
async def get_activity_log(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user activity log."""
    return []

@router.get("/me/export")
async def export_user_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Export user data."""
    return {
        "user": current_user,
        "accounts": [
            acc for acc in data_manager.accounts 
            if acc["user_id"] == current_user["id"]
        ],
        "transactions": []
    }

@router.get("/me/stats")
async def get_user_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user statistics."""
    user_accounts = [
        acc for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    user_transactions = [
        t for t in data_manager.transactions
        if any(t.get("account_id") == acc["id"] for acc in user_accounts)
    ]
    
    return {
        "total_accounts": len(user_accounts),
        "total_balance": sum(acc["balance"] for acc in user_accounts),
        "total_transactions": len(user_transactions),
        "accounts": user_accounts,
        "transactions": user_transactions,
        "budgets": 0,
        "goals": 0,
        "contacts": 0,
        "member_since": current_user.get("created_at", datetime.utcnow().isoformat()),
        "days_active": 1
    }

@router.delete("/me")
async def delete_own_account(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete own account."""
    user = next(
        (u for u in data_manager.users if u["id"] == current_user["id"]),
        None
    )
    
    if user:
        data_manager.users.remove(user)
        data_manager.sessions = [s for s in data_manager.sessions if s["user_id"] != current_user["id"]]
        
    return {"message": "Account deleted successfully"}


# Add routes without /me prefix that tests expect
@router.get("/preferences")
async def get_preferences_alt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user preferences (alternative path)."""
    return {
        "theme": "light",
        "notifications": True,
        "language": "en",
        "currency": "USD",
        "timezone": "America/New_York"
    }

@router.put("/preferences")
async def update_preferences_alt(
    preferences: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user preferences (alternative path)."""
    # Return the preferences with all fields
    result = {
        "theme": preferences.get("theme", "light"),
        "notifications": preferences.get("notifications", True),
        "language": preferences.get("language", "en"),
        "currency": preferences.get("currency", "USD"),
        "timezone": preferences.get("timezone", "America/New_York")
    }
    return result

@router.get("/security")
async def get_security_alt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get security settings (alternative path)."""
    return {
        "two_factor_enabled": False,
        "last_login": datetime.utcnow().isoformat(),
        "active_sessions": 1
    }

@router.get("/activity")
async def get_activity_alt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get activity log (alternative path)."""
    return []

@router.get("/export")
async def export_data_alt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Export user data (alternative path)."""
    return {
        "user": current_user,
        "accounts": [
            acc for acc in data_manager.accounts 
            if acc["user_id"] == current_user["id"]
        ],
        "transactions": []
    }

@router.post("/change-password")
async def change_password_alt(
    data: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Change password (alternative path)."""
    return await change_password(data, current_user)

@router.get("/stats") 
async def get_stats_alt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user statistics (alternative path)."""
    user_accounts = [
        acc for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    user_transactions = [
        t for t in data_manager.transactions
        if any(t.get("account_id") == acc["id"] for acc in user_accounts)
    ]
    
    return {
        "total_accounts": len(user_accounts),
        "total_balance": sum(acc["balance"] for acc in user_accounts),
        "total_transactions": len(user_transactions),
        "transactions": user_transactions,  # Add this field
        "accounts": user_accounts
    }

@router.put("/profile")
async def update_profile_alt(
    request: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update profile (alternative path)."""
    return await update_current_user(request, current_user)

@router.get("")
async def get_all_users(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all users (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = []
    for u in data_manager.users:
        full_name_parts = u.get("full_name", "").split(None, 1)
        users.append({
            "id": u["id"],
            "username": u["username"],
            "email": u["email"],
            "first_name": full_name_parts[0] if full_name_parts else "",
            "last_name": full_name_parts[1] if len(full_name_parts) > 1 else "",
            "is_active": u.get("is_active", True),
            "is_admin": u.get("is_admin", False),
            "created_at": u.get("created_at")
        })
    
    return users

@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific user."""
    if user_id != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = next(
        (u for u in data_manager.users if u["id"] == user_id),
        None
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    full_name_parts = user.get("full_name", "").split(None, 1)
    
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": full_name_parts[0] if full_name_parts else "",
        "last_name": full_name_parts[1] if len(full_name_parts) > 1 else "",
        "is_active": user.get("is_active", True),
        "is_admin": user.get("is_admin", False),
        "created_at": user.get("created_at")
    }

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete user (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user = next(
        (u for u in data_manager.users if u["id"] == user_id),
        None
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    data_manager.users.remove(user)
    return {"message": "User deleted successfully"}
