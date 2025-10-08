"""
Enhanced session management with concurrent login detection and device tracking.
Provides secure session handling for banking applications with multi-device support.
"""
import secrets
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status

from .auth import session_auth
from ..services.audit_logger import audit_logger, AuditEventType, AuditSeverity


class DeviceInfo:
    """Device information for session tracking."""

    def __init__(self, user_agent: str, ip_address: str):
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.fingerprint = self._generate_fingerprint(user_agent, ip_address)
        self.first_seen = time.time()
        self.last_seen = time.time()

    def _generate_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Generate device fingerprint."""
        import hashlib
        data = f"{user_agent}:{ip_address}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def update_last_seen(self):
        """Update last seen timestamp."""
        self.last_seen = time.time()

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "fingerprint": self.fingerprint,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "first_seen": datetime.fromtimestamp(self.first_seen).isoformat(),
            "last_seen": datetime.fromtimestamp(self.last_seen).isoformat()
        }


class SessionInfo:
    """Session information with enhanced security features."""

    def __init__(self, session_id: str, user_id: int, username: str, device_info: DeviceInfo):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.device_info = device_info
        self.created_at = time.time()
        self.last_activity = time.time()
        self.is_active = True
        self.login_count = 1
        self.concurrent_warning_sent = False

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()
        self.device_info.update_last_seen()

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "device": self.device_info.to_dict(),
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "last_activity": datetime.fromtimestamp(self.last_activity).isoformat(),
            "is_active": self.is_active,
            "duration_minutes": int((time.time() - self.created_at) / 60)
        }


class EnhancedSessionManager:
    """Enhanced session manager with concurrent login detection and device tracking."""

    def __init__(self):
        # Store sessions: {session_id: SessionInfo}
        self.sessions: Dict[str, SessionInfo] = {}

        # User to sessions mapping: {user_id: Set[session_id]}
        self.user_sessions: Dict[int, Set[str]] = {}

        # Device tracking: {user_id: {device_fingerprint: DeviceInfo}}
        self.user_devices: Dict[int, Dict[str, DeviceInfo]] = {}

        # Configuration
        self.max_concurrent_sessions = 3  # Max sessions per user
        self.session_timeout = 3600  # 1 hour of inactivity
        self.absolute_timeout = 28800  # 8 hours absolute session limit
        self.max_devices_per_user = 5  # Max remembered devices per user

    def _get_device_info(self, request: Request) -> DeviceInfo:
        """Extract device information from request."""
        user_agent = request.headers.get("user-agent", "unknown")

        # Try to get real IP from headers
        ip_address = request.headers.get("x-forwarded-for")
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.headers.get("x-real-ip") or str(request.client.host)

        return DeviceInfo(user_agent, ip_address)

    def _is_suspicious_login(self, user_id: int, device_info: DeviceInfo) -> bool:
        """Check if login attempt is suspicious."""
        if user_id not in self.user_devices:
            return False  # First time login, not suspicious

        user_devices = self.user_devices[user_id]

        # Check if this is a completely new device
        if device_info.fingerprint not in user_devices:
            # New device from new location might be suspicious
            known_ips = {dev.ip_address for dev in user_devices.values()}
            if device_info.ip_address not in known_ips:
                return True

        return False

    def create_session(self, user_id: int, username: str, request: Request) -> str:
        """Create a new session with concurrent login detection."""
        device_info = self._get_device_info(request)

        # Check for suspicious login
        if self._is_suspicious_login(user_id, device_info):
            audit_logger.log_security_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                user_id=user_id,
                request=request,
                details={
                    "reason": "login_from_new_device_and_location",
                    "device_fingerprint": device_info.fingerprint,
                    "ip_address": device_info.ip_address
                },
                severity=AuditSeverity.HIGH
            )

        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        # Check concurrent session limits
        existing_sessions = self.user_sessions.get(user_id, set())
        if len(existing_sessions) >= self.max_concurrent_sessions:
            self._handle_concurrent_login(user_id, existing_sessions, request)

        # Generate new session
        session_id = secrets.token_urlsafe(32)
        session_info = SessionInfo(session_id, user_id, username, device_info)

        # Store session
        self.sessions[session_id] = session_info

        # Update user session mapping
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        # Track device
        if user_id not in self.user_devices:
            self.user_devices[user_id] = {}
        self.user_devices[user_id][device_info.fingerprint] = device_info

        # Clean up old devices if too many
        if len(self.user_devices[user_id]) > self.max_devices_per_user:
            self._cleanup_old_devices(user_id)

        # Log successful login
        audit_logger.log_authentication(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            request=request,
            success=True,
            details={
                "session_id": session_id,
                "device_fingerprint": device_info.fingerprint,
                "concurrent_sessions": len(existing_sessions) + 1
            }
        )

        return session_id

    def _handle_concurrent_login(self, user_id: int, existing_sessions: Set[str], request: Request):
        """Handle concurrent login detection."""
        # Log concurrent login attempt
        audit_logger.log_security_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            request=request,
            details={
                "reason": "concurrent_login_limit_exceeded",
                "existing_sessions": len(existing_sessions),
                "limit": self.max_concurrent_sessions
            },
            severity=AuditSeverity.MEDIUM
        )

        # Terminate oldest session
        oldest_session_id = None
        oldest_time = float('inf')

        for session_id in existing_sessions:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if session.created_at < oldest_time:
                    oldest_time = session.created_at
                    oldest_session_id = session_id

        if oldest_session_id:
            self.terminate_session(oldest_session_id, reason="concurrent_login_limit")

    def get_session(self, session_id: str, request: Optional[Request] = None) -> Optional[SessionInfo]:
        """Get session information with activity tracking."""
        if session_id not in self.sessions:
            return None

        session_info = self.sessions[session_id]

        # Check if session is expired
        current_time = time.time()

        # Check inactivity timeout
        if current_time - session_info.last_activity > self.session_timeout:
            self.terminate_session(session_id, reason="inactivity_timeout")
            return None

        # Check absolute timeout
        if current_time - session_info.created_at > self.absolute_timeout:
            self.terminate_session(session_id, reason="absolute_timeout")
            return None

        # Update activity
        session_info.update_activity()

        # Validate device if request provided
        if request:
            current_device = self._get_device_info(request)
            if current_device.fingerprint != session_info.device_info.fingerprint:
                # Device mismatch - potential session hijacking
                audit_logger.log_security_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    user_id=session_info.user_id,
                    request=request,
                    details={
                        "reason": "device_fingerprint_mismatch",
                        "session_device": session_info.device_info.fingerprint,
                        "current_device": current_device.fingerprint
                    },
                    severity=AuditSeverity.CRITICAL
                )

                self.terminate_session(session_id, reason="device_mismatch")
                return None

        return session_info

    def terminate_session(self, session_id: str, reason: str = "manual", user_id: Optional[int] = None):
        """Terminate a specific session."""
        if session_id not in self.sessions:
            return

        session_info = self.sessions[session_id]
        session_info.is_active = False

        # Remove from user sessions
        if session_info.user_id in self.user_sessions:
            self.user_sessions[session_info.user_id].discard(session_id)

        # Log session termination
        audit_logger.log_event(
            event_type=AuditEventType.LOGOUT,
            user_id=session_info.user_id,
            details={
                "session_id": session_id,
                "termination_reason": reason,
                "session_duration": int(time.time() - session_info.created_at),
                "initiated_by": "user" if reason == "manual" else "system"
            }
        )

        # Remove from sessions
        del self.sessions[session_id]

    def terminate_all_user_sessions(self, user_id: int, except_session: Optional[str] = None):
        """Terminate all sessions for a user."""
        if user_id not in self.user_sessions:
            return

        sessions_to_terminate = self.user_sessions[user_id].copy()
        if except_session:
            sessions_to_terminate.discard(except_session)

        for session_id in sessions_to_terminate:
            self.terminate_session(session_id, reason="user_requested")

    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get all active sessions for a user."""
        if user_id not in self.user_sessions:
            return []

        active_sessions = []
        for session_id in self.user_sessions[user_id].copy():
            if session_id in self.sessions:
                session_info = self.sessions[session_id]
                if session_info.is_active:
                    active_sessions.append(session_info.to_dict())
                else:
                    # Clean up inactive session
                    self.user_sessions[user_id].discard(session_id)

        return active_sessions

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []

        for session_id, session_info in self.sessions.items():
            # Check for timeout
            if (current_time - session_info.last_activity > self.session_timeout or
                current_time - session_info.created_at > self.absolute_timeout):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.terminate_session(session_id, reason="expired")

    def _cleanup_old_devices(self, user_id: int):
        """Clean up oldest remembered devices."""
        if user_id not in self.user_devices:
            return

        devices = self.user_devices[user_id]
        if len(devices) <= self.max_devices_per_user:
            return

        # Sort by last seen time and keep only the most recent
        sorted_devices = sorted(
            devices.items(),
            key=lambda x: x[1].last_seen,
            reverse=True
        )

        # Keep only the most recent devices
        self.user_devices[user_id] = dict(sorted_devices[:self.max_devices_per_user])

    def get_security_summary(self, user_id: int) -> Dict:
        """Get security summary for a user."""
        active_sessions = len(self.user_sessions.get(user_id, set()))
        known_devices = len(self.user_devices.get(user_id, {}))

        # Get recent audit events
        recent_events = audit_logger.get_user_audit_trail(
            user_id=user_id,
            start_time=time.time() - 86400,  # Last 24 hours
            limit=50
        )

        suspicious_events = [
            event for event in recent_events
            if event.get('severity') in ['high', 'critical']
        ]

        return {
            "user_id": user_id,
            "active_sessions": active_sessions,
            "known_devices": known_devices,
            "recent_events": len(recent_events),
            "suspicious_events": len(suspicious_events),
            "last_login": max([s.created_at for s in self.sessions.values() if s.user_id == user_id], default=0),
            "generated_at": datetime.utcnow().isoformat()
        }


# Global enhanced session manager
enhanced_session_manager = EnhancedSessionManager()