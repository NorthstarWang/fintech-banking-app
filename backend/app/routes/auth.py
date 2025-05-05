from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from typing import Any
from datetime import datetime

from ..storage.memory_adapter import db
from ..models import User, UserRole
from ..models import UserCreate, UserLogin, UserResponse
from ..utils.auth import auth_handler, session_auth, get_current_user
from ..utils.validators import validate_email, ValidationError
from ..utils.session_manager import session_manager

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserCreate, db_session: Any = Depends(db.get_db_dependency)):
    """Register a new user"""
    # Get session ID for logging
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Validate email format
    if not validate_email(user_data.email):
        raise ValidationError("Invalid email format")
    
    # Check if username exists
    existing_user = db_session.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    hashed_password = auth_handler.get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        currency=user_data.currency,
        timezone=user_data.timezone,
        role=UserRole.USER,
        is_active=True
    )
    
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    
    # Log user creation
    
    return UserResponse.from_orm(new_user)

@router.post("/login")
async def login(request: Request, response: Response, credentials: UserLogin, 
                db_session: Any = Depends(db.get_db_dependency)):
    """Login user and return token"""
    # Get session ID for logging
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Find user by username
    user = db_session.query(User).filter(User.username == credentials.username).first()
    
    if not user or not auth_handler.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db_session.commit()
    
    # Generate JWT token
    token = auth_handler.encode_token(user.id, user.username)
    
    # Also create session for easier testing
    session_id = session_auth.create_session(user.id, user.username)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400  # 24 hours
    )
    
    # Set auth token cookie as well
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400  # 24 hours
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    # Get session ID
    session_id = request.cookies.get("session_id")
    
    # Delete session
    if session_id:
        session_auth.delete_session(session_id)
    
    # Clear cookies
    response.delete_cookie("session_id")
    response.delete_cookie("auth_token")
    
    return {"message": "Successfully logged out"}

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
async def update_profile(
    request: Request,
    user_update: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update current user profile"""
    # Get session ID for logging
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    allowed_fields = ['first_name', 'last_name', 'phone', 'currency', 'timezone']
    for field in allowed_fields:
        if field in user_update and user_update[field] is not None:
            setattr(user, field, user_update[field])
    
    # Update email if provided and valid
    if 'email' in user_update and user_update['email']:
        if not validate_email(user_update['email']):
            raise ValidationError("Invalid email format")
        
        # Check if email is already taken
        existing = db_session.query(User).filter(
            User.email == user_update['email'],
            User.id != user.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        user.email = user_update['email']
    
    user.updated_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(user)
    
    return UserResponse.from_orm(user)

@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Change user password"""
    old_password = password_data.get('old_password')
    new_password = password_data.get('new_password')
    
    if not old_password or not new_password:
        raise ValidationError("Both old and new passwords are required")
    
    if len(new_password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not auth_handler.verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Update password
    user.password_hash = auth_handler.get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db_session.commit()
    
    return {"message": "Password successfully changed"}