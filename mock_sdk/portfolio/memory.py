# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Memory Storage
# Licensing: Contact [Your Email]

"""
In-Memory Storage Implementation
Default storage backend for development and testing
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import weakref
import threading

from . import BaseStorage, StorageRecord, StorageError, ConnectionError, RecordNotFoundError


class InMemoryStorage(BaseStorage):
    """
    In-memory storage implementation
    
    This is the default storage backend that stores data in memory.
    It's suitable for development, testing, and single-process applications.
    """
    
    def __init__(self, max_records: int = 10000, cleanup_interval: int = 300):
        """
        Initialize in-memory storage
        
        Args:
            max_records: Maximum number of records to store
            cleanup_interval: Interval in seconds for cleanup tasks
        """
        self.max_records = max_records
        self.cleanup_interval = cleanup_interval
        self._storage: Dict[str, Dict[str, StorageRecord]] = {}
        self._lock = threading.RLock()
        self._connected = False
        self._cleanup_task = None
    
    async def connect(self) -> bool:
        """Establish connection (always successful for in-memory)"""
        with self._lock:
            self._connected = True
            self._storage = {}
            
            # Start cleanup task
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            return True
    
    async def disconnect(self) -> bool:
        """Close connection and cleanup resources"""
        with self._lock:
            self._connected = False
            
            # Cancel cleanup task
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Clear storage
            self._storage.clear()
            return True
    
    async def create(self, collection: str, record_id: str, data: Dict[str, Any], 
                    expires_at: Optional[datetime] = None) -> bool:
        """Create a new record"""
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
        with self._lock:
            if collection not in self._storage:
                self._storage[collection] = {}
            
            # Check if record already exists
            if record_id in self._storage[collection]:
                return False
            
            # Check max records limit
            if len(self._storage[collection]) >= self.max_records:
                # Remove oldest record
                oldest_id = min(self._storage[collection].keys(), 
                              key=lambda k: self._storage[collection][k].created_at)
                del self._storage[collection][oldest_id]
            
            now = datetime.now()
            record = StorageRecord(
                id=record_id,
                data=data.copy(),
                created_at=now,
                updated_at=now,
                expires_at=expires_at
            )
            
            self._storage[collection][record_id] = record
            return True
    
    async def read(self, collection: str, record_id: str) -> Optional[StorageRecord]:
        """Read a record by ID"""
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
        with self._lock:
            if collection not in self._storage:
                return None
            
            record = self._storage[collection].get(record_id)
            if record is None:
                return None
            
            # Check if expired
            if record.expires_at and record.expires_at < datetime.now():
                del self._storage[collection][record_id]
                return None
            
            return record
    
    async def update(self, collection: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing record"""
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
        with self._lock:
            if collection not in self._storage:
                return False
            
            record = self._storage[collection].get(record_id)
            if record is None:
                return False
            
            # Check if expired
            if record.expires_at and record.expires_at < datetime.now():
                del self._storage[collection][record_id]
                return False
            
            # Update record
            record.data = data.copy()
            record.updated_at = datetime.now()
            return True
    
    async def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record by ID"""
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
        with self._lock:
            if collection not in self._storage:
                return False
            
            if record_id in self._storage[collection]:
                del self._storage[collection][record_id]
                return True
            
            return False
    
    async def list_all(self, collection: str) -> List[StorageRecord]:
        """List all records in a collection"""
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
        with self._lock:
            if collection not in self._storage:
                return []
            
            now = datetime.now()
            records = []
            
            # Filter out expired records
            for record_id, record in list(self._storage[collection].items()):
                if record.expires_at and record.expires_at < now:
                    del self._storage[collection][record_id]
                else:
                    records.append(record)
            
            return records
    
    async def query(self, collection: str, filters: Dict[str, Any]) -> List[StorageRecord]:
        """Query records with filters"""
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
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
        if not self._connected:
            raise ConnectionError("Storage not connected")
        
        with self._lock:
            if collection not in self._storage:
                return 0
            
            now = datetime.now()
            expired_ids = []
            
            for record_id, record in self._storage[collection].items():
                if record.expires_at and record.expires_at < now:
                    expired_ids.append(record_id)
            
            for record_id in expired_ids:
                del self._storage[collection][record_id]
            
            return len(expired_ids)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check storage backend health"""
        with self._lock:
            total_records = sum(len(records) for records in self._storage.values())
            
            return {
                "status": "healthy" if self._connected else "disconnected",
                "backend": "in_memory",
                "total_collections": len(self._storage),
                "total_records": total_records,
                "max_records": self.max_records,
                "memory_usage_estimate": total_records * 1024  # Rough estimate
            }
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task for expired records"""
        while self._connected:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._connected:
                    break
                
                # Cleanup expired records from all collections
                for collection in list(self._storage.keys()):
                    await self.cleanup_expired(collection)
                    
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue cleanup
                continue


def create_in_memory_storage(max_records: int = 10000, cleanup_interval: int = 300) -> InMemoryStorage:
    """Create a new in-memory storage instance"""
    return InMemoryStorage(max_records, cleanup_interval)
