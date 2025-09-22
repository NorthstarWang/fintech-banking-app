"""
Mock implementation for notifications routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
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
async def get_notifications(current_user: Dict[str, Any] = Depends(get_current_user)):
    return []

@router.post("", status_code=201)
async def create_notification(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"id": "1", "message": "Notification created"}

@router.get("/{id}")
async def get_notification(id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"id": id, "message": "Test notification"}

@router.put("/{id}")
async def update_notification(id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"id": id, "message": "Updated"}

@router.delete("/{id}")
async def delete_notification(id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"message": "Deleted successfully"}
