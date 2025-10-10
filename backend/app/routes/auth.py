from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ..models import User, UserCreate, UserLogin, UserResponse, UserRole
from ..services.audit_logger import AuditEventType, audit_logger
from ..storage.memory_adapter import db
from ..utils.auth import auth_handler, get_current_user, session_auth
from ..utils.enhanced_session_manager import enhanced_session_manager
from ..utils.mfa import mfa_manager
from ..utils.validators import ValidationError, validate_email

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserCreate, db_session: Any = Depends(db.get_db_dependency)):
    """Register a new user"""
    # Get session ID for logging

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
        if existing_user.email == user_data.email:
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

    # Create session for dual auth support
    session_id = session_auth.create_session(user.id, user.username)

    # Set session cookie
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
    # Get session ID from cookie
    session_id = request.cookies.get('session_id')

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
    if user_update.get('email'):
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


# Multi-Factor Authentication Routes
@router.post("/mfa/setup")
async def setup_mfa(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Setup MFA for the current user"""
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if mfa_manager.is_mfa_enabled(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled for this account"
        )

    setup_data = mfa_manager.setup_mfa(user.id, user.username, user.email)

    audit_logger.log_event(
        event_type=AuditEventType.MFA_ENABLED,
        user_id=user.id,
        request=request,
        details={"setup_initiated": True}
    )

    return {
        "setup_token": setup_data["setup_token"],
        "qr_code": setup_data["qr_code"],
        "manual_entry_key": setup_data["secret"],
        "backup_codes": setup_data["backup_codes"]
    }


@router.post("/mfa/verify-setup")
async def verify_mfa_setup(
    request: Request,
    setup_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Verify MFA setup and enable MFA"""
    setup_token = setup_data.get("setup_token")
    verification_code = setup_data.get("verification_code")

    if not setup_token or not verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup token and verification code are required"
        )

    try:
        mfa_manager.verify_and_enable_mfa(setup_token, verification_code)

        audit_logger.log_event(
            event_type=AuditEventType.MFA_ENABLED,
            user_id=current_user['user_id'],
            request=request,
            details={"setup_completed": True}
        )

        return {"message": "MFA has been successfully enabled"}

    except HTTPException as e:
        audit_logger.log_event(
            event_type=AuditEventType.MFA_ENABLED,
            user_id=current_user['user_id'],
            request=request,
            success=False,
            error_message=e.detail,
            details={"setup_failed": True}
        )
        raise


@router.post("/mfa/verify")
async def verify_mfa(
    request: Request,
    mfa_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Verify MFA code during login"""
    user_id = current_user['user_id']
    code = mfa_data.get("code")
    backup_code = mfa_data.get("backup_code")
    trust_device = mfa_data.get("trust_device", False)

    if not code and not backup_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either TOTP code or backup code is required"
        )

    verified = False
    method_used = ""

    try:
        if code:
            verified = mfa_manager.verify_totp(user_id, code)
            method_used = "totp"
        elif backup_code:
            verified = mfa_manager.verify_backup_code(user_id, backup_code)
            method_used = "backup_code"

        if verified:
            # Trust device if requested
            if trust_device:
                user_agent = request.headers.get("user-agent", "")
                ip_address = str(request.client.host)
                mfa_manager.trust_device(user_id, user_agent, ip_address)

            audit_logger.log_event(
                event_type=AuditEventType.MFA_VERIFICATION,
                user_id=user_id,
                request=request,
                details={
                    "method": method_used,
                    "device_trusted": trust_device
                }
            )

            return {
                "message": "MFA verification successful",
                "device_trusted": trust_device
            }
        audit_logger.log_event(
            event_type=AuditEventType.MFA_VERIFICATION,
            user_id=user_id,
            request=request,
            success=False,
            details={
                "method": method_used,
                "failure_reason": "invalid_code"
            }
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code"
        )

    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.MFA_VERIFICATION,
            user_id=user_id,
            request=request,
            success=False,
            error_message=str(e)
        )
        raise


@router.post("/mfa/disable")
async def disable_mfa(
    request: Request,
    password_data: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Disable MFA for the current user"""
    user_id = current_user['user_id']
    password = password_data.get("password")

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required to disable MFA"
        )

    user = db_session.query(User).filter(User.id == user_id).first()

    if not user or not auth_handler.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    if not mfa_manager.is_mfa_enabled(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account"
        )

    mfa_manager.disable_mfa(user_id)

    audit_logger.log_event(
        event_type=AuditEventType.MFA_DISABLED,
        user_id=user_id,
        request=request,
        details={"disabled_by_user": True}
    )

    return {"message": "MFA has been disabled"}


@router.get("/mfa/status")
async def get_mfa_status(current_user: dict = Depends(get_current_user)):
    """Get MFA status for the current user"""
    user_id = current_user['user_id']
    return mfa_manager.get_mfa_status(user_id)


@router.post("/mfa/backup-codes/regenerate")
async def regenerate_backup_codes(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate new backup codes"""
    user_id = current_user['user_id']

    if not mfa_manager.is_mfa_enabled(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account"
        )

    new_codes = mfa_manager.generate_new_backup_codes(user_id)

    audit_logger.log_event(
        event_type=AuditEventType.MFA_VERIFICATION,
        user_id=user_id,
        request=request,
        details={"backup_codes_regenerated": True}
    )

    return {"backup_codes": new_codes}


# Session Management Routes
@router.get("/sessions")
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    """Get all active sessions for the current user"""
    user_id = current_user['user_id']
    sessions = enhanced_session_manager.get_user_sessions(user_id)
    return {"sessions": sessions}


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Terminate a specific session"""
    enhanced_session_manager.terminate_session(session_id, "user_requested")

    audit_logger.log_event(
        event_type=AuditEventType.LOGOUT,
        user_id=current_user['user_id'],
        request=request,
        details={"session_terminated": session_id}
    )

    return {"message": "Session terminated"}


@router.delete("/sessions")
async def terminate_all_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Terminate all sessions except the current one"""
    current_session_id = request.cookies.get("session_id")
    user_id = current_user['user_id']

    enhanced_session_manager.terminate_all_user_sessions(user_id, current_session_id)

    audit_logger.log_event(
        event_type=AuditEventType.LOGOUT,
        user_id=user_id,
        request=request,
        details={"all_sessions_terminated": True}
    )

    return {"message": "All other sessions have been terminated"}


@router.get("/security/summary")
async def get_security_summary(current_user: dict = Depends(get_current_user)):
    """Get security summary for the current user"""
    user_id = current_user['user_id']
    return enhanced_session_manager.get_security_summary(user_id)
