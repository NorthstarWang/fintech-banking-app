"""Data models for authentication service."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserRegistrationRequest(BaseModel):
    """Request to register a new user."""
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"


class UserLoginRequest(BaseModel):
    """Request to login."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: int


class UserProfileResponse(BaseModel):
    """User profile information."""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    currency: str
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MFASetupResponse(BaseModel):
    """Response for MFA setup."""
    setup_token: str
    qr_code: str
    manual_entry_key: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code."""
    code: Optional[str] = None
    backup_code: Optional[str] = None
    trust_device: bool = False


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    user_id: int
    created_at: datetime
    last_active: datetime
    user_agent: str
    ip_address: str
    is_active: bool


class PasswordChangeRequest(BaseModel):
    """Request to change password."""
    old_password: str
    new_password: str
