from fastapi import Request
from datetime import datetime
from typing import Optional, Dict, Any

from ..models import SecurityEvent, SecurityEventType
# SecurityAuditLog and UserDevice models not yet implemented


def get_device_info(request: Request) -> Dict[str, Any]:
    """Extract device information from request"""
    user_agent = request.headers.get("user-agent", "")
    
    # Simple device detection (in production, use a proper user-agent parser)
    device_type = "desktop"
    if "Mobile" in user_agent:
        device_type = "mobile"
    elif "Tablet" in user_agent:
        device_type = "tablet"
    
    os = "Unknown"
    if "Windows" in user_agent:
        os = "Windows"
    elif "Mac" in user_agent:
        os = "macOS"
    elif "Linux" in user_agent:
        os = "Linux"
    elif "Android" in user_agent:
        os = "Android"
    elif "iOS" in user_agent or "iPhone" in user_agent:
        os = "iOS"
    
    browser = "Unknown"
    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        browser = "Safari"
    elif "Edge" in user_agent:
        browser = "Edge"
    
    return {
        "device_type": device_type,
        "os": os,
        "browser": browser,
        "user_agent": user_agent
    }


def get_or_create_device(
    db_session: Any,
    user_id: int,
    request: Request,
    device_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get or create a user device record (placeholder until UserDevice model is implemented)"""
    if not device_id:
        # Generate device ID from user agent and IP
        device_id = f"{user_id}_{request.client.host}_{hash(request.headers.get('user-agent', ''))}"
    
    # For now, return device info as dict
    device_info = get_device_info(request)
    return {
        "id": device_id,
        "user_id": user_id,
        "device_name": f"{device_info['browser']} on {device_info['os']}",
        "device_type": device_info["device_type"],
        "os": device_info["os"],
        "browser": device_info["browser"],
        "ip_address": request.client.host,
        "location": "Unknown"  # In production, use IP geolocation
    }


def log_security_event(
    db_session: Any,
    user_id: int,
    event_type: SecurityEventType,
    request: Request,
    success: bool = True,
    failure_reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    device_id: Optional[str] = None
):
    """Log a security event"""
    # Get or create device info
    device = get_or_create_device(db_session, user_id, request, device_id)
    
    # Create security event
    security_event = SecurityEvent(
        user_id=user_id,
        event_type=event_type,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        event_metadata=metadata or {}  # Changed from metadata to event_metadata
    )
    
    db_session.add(security_event)
    db_session.commit()
    
    return security_event