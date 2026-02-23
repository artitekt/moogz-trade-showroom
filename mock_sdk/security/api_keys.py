# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: API Keys
# Licensing: Contact [Your Email]

"""
API Key Management Module
Enterprise-grade API key generation and management
"""

import secrets
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json


class KeyType(Enum):
    """API key types"""
    READ_ONLY = "read_only"
    TRADING = "trading"
    ADMIN = "admin"


class KeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class APIKey:
    """API key data model"""
    key_id: str
    key_hash: str
    name: str
    key_type: KeyType
    permissions: List[str]
    user_id: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    status: KeyStatus
    rate_limit: int  # requests per minute


class APIKeyManager:
    """Enterprise API key manager"""
    
    def __init__(self, default_rate_limit: int = 1000):
        """
        Initialize API key manager
        
        Args:
            default_rate_limit: Default rate limit (requests per minute)
        """
        self.default_rate_limit = default_rate_limit
        self.api_keys: Dict[str, APIKey] = {}
        self.usage_tracking: Dict[str, List[float]] = {}
    
    def generate_api_key(self, user_id: str, name: str, key_type: KeyType,
                        permissions: List[str] = None, expires_in_days: int = 365,
                        rate_limit: int = None) -> tuple[str, APIKey]:
        """
        Generate a new API key
        
        Args:
            user_id: User ID
            name: Key name/description
            key_type: Type of key
            permissions: List of permissions
            expires_in_days: Days until expiry
            rate_limit: Rate limit (requests per minute)
            
        Returns:
            Tuple of (api_key, APIKey object)
        """
        # Generate secure random key
        api_key = f"mt_{secrets.token_urlsafe(32)}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Set default permissions based on key type
        if not permissions:
            permissions = self._get_default_permissions(key_type)
        
        # Set expiry
        if expires_in_days > 0:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        elif expires_in_days < 0:
            # Negative days means already expired
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        else:
            expires_at = None
        
        # Create API key object
        key_obj = APIKey(
            key_id=secrets.token_urlsafe(16),
            key_hash=key_hash,
            name=name,
            key_type=key_type,
            permissions=permissions,
            user_id=user_id,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_used=None,
            usage_count=0,
            status=KeyStatus.ACTIVE,
            rate_limit=rate_limit or self.default_rate_limit
        )
        
        self.api_keys[key_hash] = key_obj
        return api_key, key_obj
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key
        
        Args:
            api_key: The API key to validate
            
        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_obj = self.api_keys.get(key_hash)
        
        if not key_obj:
            return None
        
        # Check status
        if key_obj.status != KeyStatus.ACTIVE:
            return None
        
        # Check expiry
        if key_obj.expires_at and key_obj.expires_at < datetime.now():
            return None
        
        # Update usage
        key_obj.last_used = datetime.now()
        key_obj.usage_count += 1
        
        # Track usage for rate limiting
        self._track_usage(key_hash)
        
        return key_obj
    
    def check_rate_limit(self, api_key: str) -> bool:
        """
        Check if API key is within rate limit
        
        Args:
            api_key: The API key to check
            
        Returns:
            True if within limit, False otherwise
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_obj = self.api_keys.get(key_hash)
        
        if not key_obj:
            return False
        
        # Get usage in last minute
        now = time.time()
        one_minute_ago = now - 60
        
        usage_times = self.usage_tracking.get(key_hash, [])
        recent_usage = [t for t in usage_times if t > one_minute_ago]
        
        return len(recent_usage) < key_obj.rate_limit
    
    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key
        
        Args:
            api_key: The API key to revoke
            
        Returns:
            True if revoked, False if not found
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_obj = self.api_keys.get(key_hash)
        
        if key_obj:
            key_obj.status = KeyStatus.REVOKED
            return True
        return False
    
    def suspend_api_key(self, api_key: str) -> bool:
        """
        Suspend an API key
        
        Args:
            api_key: The API key to suspend
            
        Returns:
            True if suspended, False if not found
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_obj = self.api_keys.get(key_hash)
        
        if key_obj:
            key_obj.status = KeyStatus.SUSPENDED
            return True
        return False
    
    def activate_api_key(self, api_key: str) -> bool:
        """
        Activate a suspended API key
        
        Args:
            api_key: The API key to activate
            
        Returns:
            True if activated, False if not found
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_obj = self.api_keys.get(key_hash)
        
        if key_obj and key_obj.status == KeyStatus.SUSPENDED:
            key_obj.status = KeyStatus.ACTIVE
            return True
        return False
    
    def get_user_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        return [key for key in self.api_keys.values() if key.user_id == user_id]
    
    def get_key_info(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key information (without exposing the key)"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_obj = self.api_keys.get(key_hash)
        
        if not key_obj:
            return None
        
        return {
            "key_id": key_obj.key_id,
            "name": key_obj.name,
            "key_type": key_obj.key_type.value,
            "permissions": key_obj.permissions,
            "created_at": key_obj.created_at.isoformat(),
            "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None,
            "last_used": key_obj.last_used.isoformat() if key_obj.last_used else None,
            "usage_count": key_obj.usage_count,
            "status": key_obj.status.value,
            "rate_limit": key_obj.rate_limit
        }
    
    def _get_default_permissions(self, key_type: KeyType) -> List[str]:
        """Get default permissions for key type"""
        permissions_map = {
            KeyType.READ_ONLY: ["market_data:read", "portfolio:read"],
            KeyType.TRADING: ["market_data:read", "portfolio:read", "orders:create", "orders:read"],
            KeyType.ADMIN: ["*"]  # All permissions
        }
        return permissions_map.get(key_type, [])
    
    def _track_usage(self, key_hash: str):
        """Track API key usage for rate limiting"""
        now = time.time()
        if key_hash not in self.usage_tracking:
            self.usage_tracking[key_hash] = []
        
        self.usage_tracking[key_hash].append(now)
        
        # Clean old usage data (older than 5 minutes)
        five_minutes_ago = now - 300
        self.usage_tracking[key_hash] = [
            t for t in self.usage_tracking[key_hash] if t > five_minutes_ago
        ]


# Convenience functions
def create_api_key_manager(rate_limit: int = 1000) -> APIKeyManager:
    """Create a new API key manager"""
    return APIKeyManager(rate_limit)
