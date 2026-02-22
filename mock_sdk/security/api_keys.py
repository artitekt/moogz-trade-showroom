"""
Mock API Key Management Module
Simulated API key management for demo purposes
"""

import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime


class APIKeyManager:
    """Mock API key manager for demo purposes"""
    
    def __init__(self):
        """Initialize mock API key manager"""
        self.mock_keys = {}
    
    def generate_api_key(self, user_id: str, permissions: List[str]) -> Dict[str, Any]:
        """Mock API key generation"""
        api_key = f"mk_{secrets.token_hex(24)}"
        key_id = f"key_{secrets.token_hex(8)}"
        
        self.mock_keys[api_key] = {
            "key_id": key_id,
            "user_id": user_id,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        return {
            "api_key": api_key,
            "key_id": key_id,
            "permissions": permissions,
            "created_at": datetime.now().isoformat()
        }
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Mock API key validation"""
        if api_key in self.mock_keys:
            key_data = self.mock_keys[api_key]
            return {
                "valid": True,
                "key_id": key_data["key_id"],
                "user_id": key_data["user_id"],
                "permissions": key_data["permissions"]
            }
        return {"valid": False}
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Mock API key revocation"""
        if api_key in self.mock_keys:
            del self.mock_keys[api_key]
            return True
        return False
