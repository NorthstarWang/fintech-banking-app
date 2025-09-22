"""
Authentication routes using the mock data system.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.repositories.data_manager import data_manager

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/login")
async def login(request: LoginRequest):
    """
    Login user and create session.
    
    Args:
        request: Login credentials
        
    Returns:
        User data and session token
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
            "user": result["user"],
            "message": "Login successful"
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    Args:
        request: Registration data
        
    Returns:
        Created user data
    """
    try:
        # Convert first_name/last_name to full_name
        full_name = f"{request.first_name} {request.last_name}"
        
        user = data_manager.auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=full_name
        )
        
        # Return user data in expected format
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "first_name": request.first_name,
            "last_name": request.last_name,
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Logout current user.
    
    Args:
        authorization: Authorization header
        
    Returns:
        Success message
    """
    if not authorization or not authorization.startswith("Bearer "):
        # For session-based logout (no auth header), just return success
        return {"message": "Successfully logged out"}
        
    token = authorization.replace("Bearer ", "")
    success = data_manager.auth_service.logout(token)
    
    if success:
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(status_code=400, detail="Invalid session")

@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current user information.
    
    Args:
        authorization: Authorization header
        
    Returns:
        Current user data
    """
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
    """
    Change user password.
    
    Args:
        request: Password change data
        authorization: Authorization header
        
    Returns:
        Success message
    """
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
            # Create new session after password change
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
async def get_active_sessions(authorization: Optional[str] = Header(None)):
    """
    Get all active sessions for current user.
    
    Args:
        authorization: Authorization header
        
    Returns:
        List of active sessions
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    sessions = data_manager.auth_service.get_active_sessions(user["id"])
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }

@router.post("/logout-all")
async def logout_all_sessions(authorization: Optional[str] = Header(None)):
    """
    Logout from all sessions.
    
    Args:
        authorization: Authorization header
        
    Returns:
        Success message with count
    """
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
    """
    Update user profile.
    
    Args:
        update_data: Profile update data
        authorization: Authorization header
        
    Returns:
        Updated user data
    """
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
    """
    Validate current session.
    
    Args:
        authorization: Authorization header
        
    Returns:
        Validation result
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False, "reason": "No token provided"}
        
    token = authorization.replace("Bearer ", "")
    valid = data_manager.auth_service.validate_session(token)
    
    return {
        "valid": valid,
        "reason": "Valid session" if valid else "Invalid or expired session"
    }