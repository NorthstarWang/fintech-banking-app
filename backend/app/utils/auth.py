import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from .password_utils import password_hasher

# Configuration
SECRET_KEY = "your-secret-key-here-change-in-production"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

class AuthHandler:
    security = HTTPBearer()
    secret = SECRET_KEY
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return password_hasher.hash_password(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return password_hasher.verify_password(plain_password, hashed_password)
    
    def encode_token(self, user_id: int, username: str) -> str:
        """Generate JWT token"""
        payload = {
            'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow(),
            'sub': str(user_id),
            'username': username
        }
        return jwt.encode(payload, self.secret, algorithm=ALGORITHM)
    
    def decode_token(self, token: str) -> Dict:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token has expired'
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token'
            )
    
    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = security) -> Dict:
        """Dependency for protected routes"""
        return self.decode_token(auth.credentials)
    
    def get_current_user_id(self, auth: HTTPAuthorizationCredentials = security) -> int:
        """Extract user ID from token"""
        payload = self.decode_token(auth.credentials)
        return int(payload['sub'])

# Singleton instance
auth_handler = AuthHandler()

# Standalone functions for backward compatibility
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return auth_handler.get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return auth_handler.verify_password(plain_password, hashed_password)

# Optional: Session-based authentication for simpler testing
class SessionAuth:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, user_id: int, username: str) -> str:
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'created_at': datetime.utcnow(),
            'last_accessed': datetime.utcnow()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if session_id in self.sessions:
            # Update last accessed time
            self.sessions[session_id]['last_accessed'] = datetime.utcnow()
            return self.sessions[session_id]
        return None
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_user_from_request(self, request: Request) -> Optional[Dict]:
        """Get user from session cookie"""
        session_id = request.cookies.get('session_id')
        if session_id:
            return self.get_session(session_id)
        return None
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_delete = []
        for session_id, data in self.sessions.items():
            if data['last_accessed'] < cutoff:
                to_delete.append(session_id)
        for session_id in to_delete:
            del self.sessions[session_id]

# Singleton instance
session_auth = SessionAuth()

# Dependency for getting current user (supports both JWT and session)
async def get_current_user(request: Request, token: Optional[str] = None):
    """Get current user from JWT token or session"""
    # First try JWT token (prefer explicit auth header)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = auth_handler.decode_token(token)
            return {
                'user_id': int(payload['sub']),
                'username': payload['username']
            }
        except HTTPException:
            pass
    
    # Then try session
    session_user = session_auth.get_user_from_request(request)
    if session_user:
        return session_user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )

# Optional dependency for admin-only endpoints
async def require_admin(current_user: Dict = get_current_user):
    """Require admin role"""
    from ..storage.memory_adapter import memory_storage
    from ..models import UserRole
    
    user = memory_storage.get_user_by_id(current_user['user_id'])
    
    if not user or user.get('role') != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user