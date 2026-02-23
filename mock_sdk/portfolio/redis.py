# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Redis Storage
# Licensing: Contact [Your Email]

"""
Redis Storage Implementation
Production-ready storage backend for distributed applications
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from . import BaseStorage, StorageRecord, StorageError, ConnectionError, RecordNotFoundError


class RedisStorage(BaseStorage):
    """
    Redis storage implementation
    
    This storage backend uses Redis for persistent, distributed storage.
    Suitable for production environments with multiple processes.
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None,
                 connection_pool_size: int = 10):
        """
        Initialize Redis storage
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            connection_pool_size: Connection pool size
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required. Install with: pip install redis")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.connection_pool_size = connection_pool_size
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Establish connection to Redis"""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=self.connection_pool_size
            )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            return True
            
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self) -> bool:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
        self._connected = False
        return True
    
    def _make_key(self, collection: str, record_id: str) -> str:
        """Generate Redis key for record"""
        return f"{collection}:{record_id}"
    
    def _serialize_record(self, record: StorageRecord) -> str:
        """Serialize StorageRecord to JSON"""
        return json.dumps({
            "id": record.id,
            "data": record.data,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "expires_at": record.expires_at.isoformat() if record.expires_at else None
        })
    
    def _deserialize_record(self, data: str) -> StorageRecord:
        """Deserialize JSON to StorageRecord"""
        record_dict = json.loads(data)
        return StorageRecord(
            id=record_dict["id"],
            data=record_dict["data"],
            created_at=datetime.fromisoformat(record_dict["created_at"]),
            updated_at=datetime.fromisoformat(record_dict["updated_at"]),
            expires_at=datetime.fromisoformat(record_dict["expires_at"]) if record_dict["expires_at"] else None
        )
    
    async def create(self, collection: str, record_id: str, data: Dict[str, Any], 
                    expires_at: Optional[datetime] = None) -> bool:
        """Create a new record"""
        if not self._connected or not self._client:
            raise ConnectionError("Storage not connected")
        
        key = self._make_key(collection, record_id)
        
        # Check if record already exists
        if await self._client.exists(key):
            return False
        
        now = datetime.now()
        record = StorageRecord(
            id=record_id,
            data=data.copy(),
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )
        
        serialized = self._serialize_record(record)
        
        # Set with expiration if provided
        if expires_at:
            ttl = int((expires_at - now).total_seconds())
            await self._client.setex(key, ttl, serialized)
        else:
            await self._client.set(key, serialized)
        
        return True
    
    async def read(self, collection: str, record_id: str) -> Optional[StorageRecord]:
        """Read a record by ID"""
        if not self._connected or not self._client:
            raise ConnectionError("Storage not connected")
        
        key = self._make_key(collection, record_id)
        data = await self._client.get(key)
        
        if data is None:
            return None
        
        try:
            record = self._deserialize_record(data)
            
            # Check if expired (Redis handles this automatically, but double-check)
            if record.expires_at and record.expires_at < datetime.now():
                await self._client.delete(key)
                return None
            
            return record
            
        except (json.JSONDecodeError, ValueError):
            # Corrupted data, remove it
            await self._client.delete(key)
            return None
    
    async def update(self, collection: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing record"""
        if not self._connected or not self._client:
            raise ConnectionError("Storage not connected")
        
        key = self._make_key(collection, record_id)
        existing_data = await self._client.get(key)
        
        if existing_data is None:
            return False
        
        try:
            record = self._deserialize_record(existing_data)
            
            # Check if expired
            if record.expires_at and record.expires_at < datetime.now():
                await self._client.delete(key)
                return False
            
            # Update record
            record.data = data.copy()
            record.updated_at = datetime.now()
            
            serialized = self._serialize_record(record)
            
            # Update with same expiration
            ttl = await self._client.ttl(key)
            if ttl > 0:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            
            return True
            
        except (json.JSONDecodeError, ValueError):
            # Corrupted data, remove it
            await self._client.delete(key)
            return False
    
    async def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record by ID"""
        if not self._connected or not self._client:
            raise ConnectionError("Storage not connected")
        
        key = self._make_key(collection, record_id)
        result = await self._client.delete(key)
        return result > 0
    
    async def list_all(self, collection: str) -> List[StorageRecord]:
        """List all records in a collection"""
        if not self._connected or not self._client:
            raise ConnectionError("Storage not connected")
        
        pattern = f"{collection}:*"
        keys = await self._client.keys(pattern)
        
        records = []
        for key in keys:
            data = await self._client.get(key)
            if data:
                try:
                    record = self._deserialize_record(data)
                    
                    # Check if expired
                    if record.expires_at and record.expires_at < datetime.now():
                        await self._client.delete(key)
                        continue
                    
                    records.append(record)
                    
                except (json.JSONDecodeError, ValueError):
                    # Corrupted data, remove it
                    await self._client.delete(key)
                    continue
        
        return records
    
    async def query(self, collection: str, filters: Dict[str, Any]) -> List[StorageRecord]:
        """Query records with filters"""
        all_records = await self.list_all(collection)
        filtered_records = []
        
        for record in all_records:
            match = True
            for key, value in filters.items():
                if key not in record.data or record.data[key] != value:
                    match = False
                    break
            
            if match:
                filtered_records.append(record)
        
        return filtered_records
    
    async def cleanup_expired(self, collection: str) -> int:
        """Remove expired records"""
        if not self._connected or not self._client:
            raise ConnectionError("Storage not connected")
        
        # Redis handles expired records automatically, but we can force cleanup
        pattern = f"{collection}:*"
        keys = await self._client.keys(pattern)
        
        removed_count = 0
        for key in keys:
            data = await self._client.get(key)
            if data:
                try:
                    record = self._deserialize_record(data)
                    if record.expires_at and record.expires_at < datetime.now():
                        await self._client.delete(key)
                        removed_count += 1
                        
                except (json.JSONDecodeError, ValueError):
                    # Corrupted data, remove it
                    await self._client.delete(key)
                    removed_count += 1
        
        return removed_count
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        if not self._connected or not self._client:
            return {
                "status": "disconnected",
                "backend": "redis",
                "error": "Not connected"
            }
        
        try:
            # Test Redis connection
            await self._client.ping()
            
            # Get Redis info
            info = await self._client.info()
            
            # Count records in all collections
            pattern = "*:*"
            keys = await self._client.keys(pattern)
            
            return {
                "status": "healthy",
                "backend": "redis",
                "host": f"{self.host}:{self.port}",
                "db": self.db,
                "total_keys": len(keys),
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "backend": "redis",
                "error": str(e)
            }


def create_redis_storage(host: str = "localhost", port: int = 6379, 
                        db: int = 0, password: Optional[str] = None,
                        connection_pool_size: int = 10) -> RedisStorage:
    """Create a new Redis storage instance"""
    return RedisStorage(host, port, db, password, connection_pool_size)
