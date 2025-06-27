"""
User repository for managing user and session data.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import secrets
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository for user-related operations."""
    
    def __init__(self, users: List[Dict[str, Any]], sessions: List[Dict[str, Any]]):
        """
        Initialize with users and sessions data stores.
        
        Args:
            users: List storing user data
            sessions: List storing session data
        """
        super().__init__(users)
        self.sessions = sessions
        
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user with hashed password.
        
        Args:
            user_data: User data including plaintext password
            
        Returns:
            Created user without password
        """
        # Hash the password
        if 'password' in user_data:
            user_data['password_hash'] = self._hash_password(user_data['password'])
            del user_data['password']
            
        # Set default values
        user_data.setdefault('is_active', True)
        user_data.setdefault('is_admin', False)
        user_data.setdefault('created_at', datetime.utcnow().isoformat())
        
        # Create user
        user = self.create(user_data)
        
        # Remove password_hash from response
        user_response = user.copy()
        user_response.pop('password_hash', None)
        
        return user_response
        
    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username."""
        return self.find_one_by_field('username', username)
        
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email."""
        return self.find_one_by_field('email', email)
        
    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verify user password.
        
        Args:
            username: Username to check
            password: Plaintext password to verify
            
        Returns:
            User data if password correct, None otherwise
        """
        user = self.find_by_username(username)
        if not user:
            return None
            
        # Get the actual user with password_hash
        for u in self.data_store:
            if u.get('username') == username:
                if self._verify_password(password, u.get('password_hash', '')):
                    # Return user without password_hash
                    user_response = u.copy()
                    user_response.pop('password_hash', None)
                    return user_response
        return None
        
    def create_session(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session for user.
        
        Args:
            user_id: ID of the user
            device_info: Optional device/browser information
            
        Returns:
            Session token
        """
        token = secrets.token_urlsafe(32)
        session_data = {
            'id': token,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_accessed': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'is_active': True
        }
        
        if device_info:
            session_data.update(device_info)
            
        self.sessions.append(session_data)
        return token
        
    def get_user_by_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user by session token.
        
        Args:
            token: Session token
            
        Returns:
            User data if valid session, None otherwise
        """
        # Find session
        session = None
        for s in self.sessions:
            if s.get('id') == token and s.get('is_active'):
                # Check if expired
                expires_at = datetime.fromisoformat(s['expires_at'])
                if expires_at > datetime.utcnow():
                    session = s
                    # Update last accessed
                    s['last_accessed'] = datetime.utcnow().isoformat()
                    break
                    
        if not session:
            return None
            
        # Get user
        user = self.find_by_id(session['user_id'])
        if user:
            user.pop('password_hash', None)
        return user
        
    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            token: Session token to invalidate
            
        Returns:
            True if invalidated, False if not found
        """
        for session in self.sessions:
            if session.get('id') == token:
                session['is_active'] = False
                return True
        return False
        
    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions invalidated
        """
        count = 0
        for session in self.sessions:
            if session.get('user_id') == user_id and session.get('is_active'):
                session['is_active'] = False
                count += 1
        return count
        
    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        active_sessions = []
        for session in self.sessions:
            if (session.get('user_id') == user_id and 
                session.get('is_active') and
                datetime.fromisoformat(session['expires_at']) > datetime.utcnow()):
                # Don't include the token in the response
                session_copy = session.copy()
                session_copy['id'] = session_copy['id'][:8] + '...'  # Partial token
                active_sessions.append(session_copy)
        return active_sessions
        
    def update_password(self, user_id: str, new_password: str) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password: New plaintext password
            
        Returns:
            True if updated, False if user not found
        """
        for user in self.data_store:
            if user.get('id') == user_id:
                user['password_hash'] = self._hash_password(new_password)
                user['password_changed_at'] = datetime.utcnow().isoformat()
                return True
        return False
        
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return self._hash_password(password) == password_hash