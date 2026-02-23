# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Storage
# Licensing: Contact [Your Email]

"""
Storage Module
Abstract base classes for swappable storage backends
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StorageRecord:
    """Generic storage record"""
    id: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class BaseStorage(ABC):
    """
    Abstract base class for storage backends
    
    This class defines the interface that all storage implementations must follow.
    It allows users to swap between in-memory, Redis, PostgreSQL, or other storage
    backends without changing the application code.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to storage backend
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to storage backend
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, collection: str, record_id: str, data: Dict[str, Any], 
                    expires_at: Optional[datetime] = None) -> bool:
        """
        Create a new record
        
        Args:
            collection: Name of the collection/table
            record_id: Unique identifier for the record
            data: Data to store
            expires_at: Optional expiration time
            
        Returns:
            True if creation successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def read(self, collection: str, record_id: str) -> Optional[StorageRecord]:
        """
        Read a record by ID
        
        Args:
            collection: Name of the collection/table
            record_id: Unique identifier for the record
            
        Returns:
            StorageRecord if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, collection: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing record
        
        Args:
            collection: Name of the collection/table
            record_id: Unique identifier for the record
            data: New data to store
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, collection: str, record_id: str) -> bool:
        """
        Delete a record by ID
        
        Args:
            collection: Name of the collection/table
            record_id: Unique identifier for the record
            
        Returns:
            True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(self, collection: str) -> List[StorageRecord]:
        """
        List all records in a collection
        
        Args:
            collection: Name of the collection/table
            
        Returns:
            List of all StorageRecord objects in the collection
        """
        pass
    
    @abstractmethod
    async def query(self, collection: str, filters: Dict[str, Any]) -> List[StorageRecord]:
        """
        Query records with filters
        
        Args:
            collection: Name of the collection/table
            filters: Dictionary of field filters
            
        Returns:
            List of matching StorageRecord objects
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self, collection: str) -> int:
        """
        Remove expired records
        
        Args:
            collection: Name of the collection/table
            
        Returns:
            Number of records removed
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check storage backend health
        
        Returns:
            Dictionary with health status information
        """
        pass


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class ConnectionError(StorageError):
    """Exception raised when connection fails"""
    pass


class RecordNotFoundError(StorageError):
    """Exception raised when record is not found"""
    pass


class ValidationError(StorageError):
    """Exception raised when data validation fails"""
    pass


# Import storage implementations
from .memory import InMemoryStorage, create_in_memory_storage
from .redis import RedisStorage, create_redis_storage

__all__ = [
    # Base classes
    "BaseStorage",
    "StorageRecord",
    
    # Exceptions
    "StorageError",
    "ConnectionError", 
    "RecordNotFoundError",
    "ValidationError",
    
    # Implementations
    "InMemoryStorage",
    "create_in_memory_storage",
    "RedisStorage", 
    "create_redis_storage"
]
