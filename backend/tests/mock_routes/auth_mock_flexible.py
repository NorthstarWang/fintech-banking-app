"""
Flexible auth routes that handle both first_name/last_name and full_name formats.
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.repositories.data_manager import data_manager

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class FlexibleRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    # Accept either format
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('*', pre=True)
    def validate_names(cls, v, values):
        # If we have first_name/last_name but no full_name, create it
        if 'first_name' in values and 'last_name' in values and 'full_name' not in values:
            values['full_name'] = f"{values['first_name']} {values['last_name']}"
        return v
    
    def get_full_name(self) -> str:
        """Get full name from either format."""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return ""

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/login")
async def login(request: LoginRequest):
    """
    Login user and return access token.
    
    Args:
        request: Login credentials
        
    Returns:
        Access token and user data
    """
    try:
        result = data_manager.auth_service.login(
            request.username,
            request.password,
            {"device": "Web Browser", "ip": "127.0.0.1"}
        )
        
        return {
            "access_token": result["token"],
            "token_type": "bearer",
            "token": result["token"],  # Backward compatibility
            "user": result["user"],
            "message": "Login successful"
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/register", status_code=201)
async def register(request: Dict[str, Any]):
    """
    Register a new user - flexible to handle both formats.
    
    Args:
        request: Registration data (dict to handle both formats)
        
    Returns:
        Created user data
    """
    try:
        # Handle both formats
        if "first_name" in request and "last_name" in request:
            full_name = f"{request['first_name']} {request['last_name']}"
        elif "full_name" in request:
            full_name = request["full_name"]
        else:
            full_name = ""
        
        # Check if user already exists
        existing = next(
            (u for u in data_manager.users 
             if u["username"] == request["username"] or u["email"] == request["email"]),
            None
        )
        
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Register user
        user = data_manager.auth_service.register_user(
            username=request["username"],
            email=request["email"],
            password=request["password"],
            full_name=full_name
        )
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "message": "User registered successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Include all other endpoints from auth_mock.py
@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout current user."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"message": "Successfully logged out"}
        
    token = authorization.replace("Bearer ", "")
    success = data_manager.auth_service.logout(token)
    
    if success:
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(status_code=400, detail="Invalid session")

@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    authorization: Optional[str] = Header(None)
):
    """Change user password."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    try:
        success = data_manager.auth_service.change_password(
            user["id"],
            request.old_password,
            request.new_password
        )
        
        if success:
            result = data_manager.auth_service.login(
                user["username"],
                request.new_password,
                {"device": "Web Browser", "ip": "127.0.0.1"}
            )
            
            return {
                "message": "Password successfully changed",
                "token": result["token"]
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to change password")
            
    except ValueError as e:
        if "Incorrect password" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions")
async def get_sessions(authorization: Optional[str] = Header(None)):
    """Get active sessions."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    sessions = data_manager.auth_service.get_active_sessions(user["id"])
    return sessions

@router.post("/logout-all")
async def logout_all(authorization: Optional[str] = Header(None)):
    """Logout all sessions."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    count = data_manager.auth_service.logout_all_sessions(user["id"])
    
    return {
        "message": f"Logged out from {count} sessions",
        "count": count
    }

@router.put("/me")
async def update_profile(
    update_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """Update user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Update user fields
    if "first_name" in update_data or "last_name" in update_data:
        first_name = update_data.get("first_name", user.get("full_name", "").split()[0] if user.get("full_name") else "")
        last_name = update_data.get("last_name", user.get("full_name", "").split()[-1] if user.get("full_name") and len(user.get("full_name", "").split()) > 1 else "")
        user["full_name"] = f"{first_name} {last_name}".strip()
    
    # Return user with first_name and last_name fields
    full_name_parts = user.get("full_name", "").split(None, 1)
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": full_name_parts[0] if full_name_parts else "",
        "last_name": full_name_parts[1] if len(full_name_parts) > 1 else "",
        "is_active": user.get("is_active", True),
        "created_at": user["created_at"]
    }

@router.get("/validate")
async def validate_session(authorization: Optional[str] = Header(None)):
    """Validate current session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    
    if data_manager.auth_service.validate_session(token):
        return {"valid": True}
    else:
        return {"valid": False}