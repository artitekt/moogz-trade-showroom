# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Authentication
# Licensing: Contact [Your Email]

"""
Authentication Module
Enterprise-grade user authentication and session management
"""

import jwt
import bcrypt
import secrets
import time
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from dataclasses import dataclass


@dataclass
class User:
    """User data model"""
    id: str
    username: str
    email: str
    password_hash: str
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


@dataclass
class Session:
    """Session data model"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuthManager:
    """Enterprise authentication manager"""
    
    def __init__(self, secret_key: Optional[str] = None, token_expiry_hours: int = 24):
        """
        Initialize auth manager
        
        Args:
            secret_key: JWT secret key. If None, generates a new key.
            token_expiry_hours: Token expiry time in hours
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
        self.token_expiry = timedelta(hours=token_expiry_hours)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, username: str, email: str, password: str, roles: List[str] = None) -> User:
        """Create a new user"""
        user_id = secrets.token_urlsafe(16)
        password_hash = self.hash_password(password)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles or ["user"],
            created_at=datetime.now()
        )
        
        self.users[user_id] = user
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        for user in self.users.values():
            if user.username == username and user.is_active:
                if self.verify_password(password, user.password_hash):
                    user.last_login = datetime.now()
                    return user
        return None
    
    def create_session(self, user: User, ip_address: str = None, user_agent: str = None) -> Session:
        """Create a new session for user"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + self.token_expiry
        
        session = Session(
            session_id=session_id,
            user_id=user.id,
            created_at=datetime.now(),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        return session
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate session and return user"""
        session = self.sessions.get(session_id)
        if not session or session.expires_at < datetime.now():
            return None
        
        return self.users.get(session.user_id)
    
    def generate_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "roles": user.roles,
            "exp": datetime.now() + self.token_expiry,
            "iat": datetime.now()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        to_remove = [
            session_id for session_id, session in self.sessions.items()
            if session.user_id == user_id
        ]
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        return len(to_remove)
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            session_id for session_id, session in self.sessions.items()
            if session.expires_at < now
        ]
        
        for session_id in expired:
            del self.sessions[session_id]
        
        return len(expired)


# Convenience functions
def create_auth_manager(secret_key: Optional[str] = None) -> AuthManager:
    """Create a new auth manager"""
    return AuthManager(secret_key)
