"""
Mock Authentication Module
Simulated authentication for demo purposes
"""

import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class AuthManager:
    """Mock authentication manager for demo purposes"""
    
    def __init__(self):
        """Initialize mock authentication manager"""
        self.mock_sessions = {}
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Mock authentication that always succeeds in demo mode"""
        session_id = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        self.mock_sessions[session_id] = {
            "username": username,
            "expires_at": expires_at
        }
        
        return {
            "session_id": session_id,
            "username": username,
            "expires_at": expires_at.isoformat(),
            "authenticated": True
        }
    
    def validate_session(self, session_id: str) -> bool:
        """Mock session validation"""
        if session_id in self.mock_sessions:
            return datetime.now() < self.mock_sessions[session_id]["expires_at"]
        return False
    
    def logout(self, session_id: str) -> bool:
        """Mock logout"""
        if session_id in self.mock_sessions:
            del self.mock_sessions[session_id]
            return True
        return False
