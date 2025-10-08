from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime
from typing import Any

from ..storage.memory_adapter import db, or_, and_
from ..models import User, Account, Transaction, Budget, Goal, Contact, ContactStatus
from ..models import UserUpdate, UserResponse
from ..utils.auth import get_current_user, AuthHandler
from ..utils.validators import ValidationError, sanitize_string
from ..utils.session_manager import session_manager

router = APIRouter()
auth_handler = AuthHandler()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get current user profile"""
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    request: Request,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update user profile"""
    
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    if update_data.email and update_data.email != user.email:
        # Check if email already exists
        existing = db_session.query(User).filter(
            User.email == update_data.email,
            User.id != user.id
        ).first()
        
        if existing:
            raise ValidationError("Email already in use")
        
        user.email = update_data.email
    
    if update_data.first_name is not None:
        user.first_name = sanitize_string(update_data.first_name, 50)
    
    if update_data.last_name is not None:
        user.last_name = sanitize_string(update_data.last_name, 50)
    
    if update_data.phone is not None:
        user.phone = sanitize_string(update_data.phone, 20)
    
    if update_data.currency is not None:
        user.currency = update_data.currency
    
    if update_data.timezone is not None:
        user.timezone = update_data.timezone
    
    user.updated_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(user)
    
    # Log update
        }
    )
    
    return UserResponse.from_orm(user)

@router.post("/me/change-password")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Change user password"""
    
    if len(new_password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not auth_handler.verify_password(current_password, user.password_hash):
        raise ValidationError("Current password is incorrect")
    
    # Update password
    user.password_hash = auth_handler.get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db_session.commit()
    
    # Log password change
    )
    
    return {"message": "Password changed successfully"}

@router.get("/me/stats")
async def get_user_statistics(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get user account statistics"""
    # Account stats
    accounts = db_session.query(Account).filter(
        Account.user_id == current_user['user_id']
    ).all()
    
    active_accounts = [a for a in accounts if a.is_active]
    
    # Transaction stats
    total_transactions = db_session.query(Transaction).filter(
        Transaction.account_id.in_([a.id for a in accounts])
    ).count()
    
    # Calculate this month's transactions
    today = datetime.today()
    month_start = today.replace(day=1)
    
    monthly_transactions = db_session.query(Transaction).filter(
        Transaction.account_id.in_([a.id for a in accounts]),
        Transaction.transaction_date >= month_start
    ).count()
    
    # Budget stats
    active_budgets = db_session.query(Budget).filter(
        Budget.user_id == current_user['user_id'],
        Budget.is_active == True
    ).count()
    
    # Goal stats
    active_goals = db_session.query(Goal).filter(
        Goal.user_id == current_user['user_id'],
        Goal.status == "active"
    ).count()
    
    completed_goals = db_session.query(Goal).filter(
        Goal.user_id == current_user['user_id'],
        Goal.status == "completed"
    ).count()
    
    # Contact stats
    contacts = db_session.query(Contact).filter(
        Contact.user_id == current_user['user_id'],
        Contact.status == "accepted"
    ).count()
    
    # Member since
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    days_active = (datetime.utcnow() - user.created_at).days if user else 0
    
    return {
        "member_since": user.created_at if user else None,
        "days_active": days_active,
        "accounts": {
            "total": len(accounts),
            "active": len(active_accounts)
        },
        "transactions": {
            "total": total_transactions,
            "this_month": monthly_transactions
        },
        "budgets": {
            "active": active_budgets
        },
        "goals": {
            "active": active_goals,
            "completed": completed_goals
        },
        "contacts": contacts
    }

@router.delete("/me")
async def delete_user_account(
    request: Request,
    password: str,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Delete user account (soft delete)"""
    
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify password
    if not auth_handler.verify_password(password, user.password_hash):
        raise ValidationError("Password is incorrect")
    
    # Soft delete - deactivate account
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    # Deactivate all accounts
    db_session.query(Account).filter(
        Account.user_id == user.id
    ).update({"is_active": False})
    
    db_session.commit()
    
    # Log account deletion
        "users",
        user.id,
        "User account deactivated"
    )
    
    return {"message": "Account deactivated successfully"}

@router.get("/preferences")
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get user preferences"""
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return current preferences
    return {
        "currency": user.currency,
        "timezone": user.timezone,
        "notifications": {
            "email": True,  # Placeholder
            "push": True,   # Placeholder
            "sms": False    # Placeholder
        },
        "privacy": user.privacy_settings,
        "security": {
            "two_factor_enabled": user.two_factor_enabled,
            "biometric_enabled": False    # Placeholder
        }
    }

@router.put("/preferences")
async def update_user_preferences(
    request: Request,
    preferences: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update user preferences"""
    
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update basic preferences
    if "currency" in preferences:
        user.currency = preferences["currency"]
    
    if "timezone" in preferences:
        user.timezone = preferences["timezone"]
    
    # Update privacy settings if provided
    if "privacy" in preferences:
        current_privacy = user.privacy_settings or {}
        current_privacy.update(preferences["privacy"])
        user.privacy_settings = current_privacy
    
    user.updated_at = datetime.utcnow()
    db_session.commit()
    
    # Log preference update
        }
    )
    
    # Return updated preferences
    return {
        "message": "Preferences updated successfully",
        "currency": user.currency,
        "timezone": user.timezone
    }

@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get public user profile (respecting privacy settings)"""
    user = db_session.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if users are contacts
    is_contact = False
    if user_id != current_user['user_id']:
        contact = db_session.query(Contact).filter(
            or_(
                and_(
                    Contact.user_id == current_user['user_id'],
                    Contact.contact_id == user_id,
                    Contact.status == ContactStatus.ACCEPTED
                ),
                and_(
                    Contact.user_id == user_id,
                    Contact.contact_id == current_user['user_id'],
                    Contact.status == ContactStatus.ACCEPTED
                )
            )
        ).first()
        is_contact = contact is not None
    
    privacy_settings = user.privacy_settings or {
        'searchable': True,
        'show_profile_stats': True,
        'show_email': False,
        'show_full_name': True
    }
    
    # Basic profile info
    profile = {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "is_contact": is_contact,
        "is_self": user_id == current_user['user_id']
    }
    
    # Add info based on privacy settings
    if privacy_settings.get('show_full_name', True) or is_contact:
        profile["first_name"] = user.first_name
        profile["last_name"] = user.last_name
        profile["full_name"] = user.full_name
    
    if privacy_settings.get('show_email', False) or is_contact:
        profile["email"] = user.email
    
    # Add stats if allowed
    if privacy_settings.get('show_profile_stats', True) or user_id == current_user['user_id']:
        # Calculate stats
        accounts = db_session.query(Account).filter(
            Account.user_id == user_id
        ).all()
        
        total_transactions = 0
        for account in accounts:
            total_transactions += db_session.query(Transaction).filter(
                Transaction.account_id == account.id
            ).count()
        
        active_goals = db_session.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == "active"
        ).count()
        
        profile["stats"] = {
            "member_since_days": (datetime.utcnow() - user.created_at).days,
            "total_transactions": total_transactions,
            "active_goals": active_goals,
            "total_contacts": db_session.query(Contact).filter(
                Contact.user_id == user_id,
                Contact.status == ContactStatus.ACCEPTED
            ).count()
        }
    
    return profile

@router.get("/search")
async def search_users(
    query: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Search for users by username or email (for joint account creation)"""
    if not query or len(query) < 2:
        return []
    
    # Sanitize search query
    search_query = sanitize_string(query).lower()
    
    # Search for users (exclude current user and inactive users)
    users = db_session.query(User).filter(
        User.id != current_user['user_id'],
        User.is_active == True
    ).all()
    
    # Filter users by username or email containing the search query
    matching_users = []
    for user in users:
        if (search_query in user.username.lower() or 
            search_query in user.email.lower() or
            search_query in user.full_name.lower()):
            matching_users.append({
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email
            })
    
    # Limit results
    return matching_users[:limit]