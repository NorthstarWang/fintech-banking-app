"""
Mock implementation for categories routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.repositories.data_manager import data_manager

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Get current user from auth header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

@router.get("")
async def get_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all categories."""
    return data_manager.categories

@router.get("/{category_id}")
async def get_category(
    category_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific category."""
    category = next(
        (c for c in data_manager.categories if str(c["id"]) == str(category_id)),
        None
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category