# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Trading Client
# Licensing: Contact [Your Email]

"""
Trading Client Module
Enterprise-grade trading client with idempotency support
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from ..network_utils import circuit_breaker, CircuitBreakerConfig
from ..observability import trace_async_function
from ..security.api_keys import APIKeyManager


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order statuses"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order data model"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    time_in_force: str
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    filled_quantity: float = 0.0
    average_price: float = 0.0
    fills: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.fills is None:
            self.fills = []


@dataclass
class IdempotencyRecord:
    """Idempotency record for request deduplication"""
    idempotency_key: str
    request_hash: str
    response_data: Optional[Dict[str, Any]]
    created_at: datetime
    expires_at: datetime
    status: str = "processed"


class IdempotencyManager:
    """Manages idempotency keys to prevent duplicate operations"""
    
    def __init__(self, cache_ttl_hours: int = 24):
        """
        Initialize idempotency manager
        
        Args:
            cache_ttl_hours: Time to live for cached requests in hours
        """
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.idempotency_cache: Dict[str, IdempotencyRecord] = {}
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def generate_idempotency_key(self) -> str:
        """Generate a unique idempotency key"""
        return f"idemp_{uuid.uuid4().hex}_{int(time.time())}"
    
    def _hash_request(self, method: str, endpoint: str, payload: Dict[str, Any]) -> str:
        """Create hash of request for deduplication"""
        import hashlib
        request_str = f"{method}:{endpoint}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(request_str.encode()).hexdigest()
    
    async def check_and_store(self, idempotency_key: str, method: str, 
                            endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if request was already processed and store if not
        
        Args:
            idempotency_key: Unique key for request
            method: HTTP method
            endpoint: API endpoint
            payload: Request payload
            
        Returns:
            Cached response if exists, None otherwise
        """
        request_hash = self._hash_request(method, endpoint, payload)
        now = datetime.now()
        
        # Check existing record
        existing = self.idempotency_cache.get(idempotency_key)
        if existing:
            # Check if expired
            if now > existing.expires_at:
                del self.idempotency_cache[idempotency_key]
                self.logger.info(f"Expired idempotency key {idempotency_key} removed")
            else:
                # Check if request hash matches
                if existing.request_hash == request_hash:
                    self.logger.info(f"Duplicate request detected for idempotency key {idempotency_key}")
                    return existing.response_data
                else:
                    self.logger.warning(f"Idempotency key {idempotency_key} reused with different request")
                    # In production, this might be an error condition
        
        # Store new record
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_data=None,
            created_at=now,
            expires_at=now + self.cache_ttl
        )
        
        self.idempotency_cache[idempotency_key] = record
        return None
    
    async def store_response(self, idempotency_key: str, response_data: Dict[str, Any]):
        """
        Store response for idempotent request
        
        Args:
            idempotency_key: Idempotency key
            response_data: Response data to cache
        """
        record = self.idempotency_cache.get(idempotency_key)
        if record:
            record.response_data = response_data
            record.status = "completed"
            self.logger.debug(f"Stored response for idempotency key {idempotency_key}")
    
    async def cleanup_expired(self):
        """Clean up expired idempotency records"""
        now = datetime.now()
        expired_keys = []
        
        for key, record in self.idempotency_cache.items():
            if now > record.expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.idempotency_cache[key]
        
        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired idempotency records")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get idempotency cache statistics"""
        total_records = len(self.idempotency_cache)
        now = datetime.now()
        expired_count = sum(1 for r in self.idempotency_cache.values() if now > r.expires_at)
        
        return {
            "total_records": total_records,
            "active_records": total_records - expired_count,
            "expired_records": expired_count,
            "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600
        }


class TradingClient:
    """Enterprise trading client with idempotency support"""
    
    def __init__(self, base_url: str, api_key: str, 
                 idempotency_ttl_hours: int = 24,
                 max_concurrent_requests: int = 10):
        """
        Initialize trading client
        
        Args:
            base_url: Base API URL
            api_key: API key for authentication
            idempotency_ttl_hours: TTL for idempotency cache
            max_concurrent_requests: Maximum concurrent requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.logger = logging.getLogger(__name__)
        
        # Idempotency management
        self.idempotency_manager = IdempotencyManager(idempotency_ttl_hours)
        
        # API key management
        self.api_key_manager = APIKeyManager()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Initialize HTTP session"""
        if self.session:
            return
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MOOGZTrade-SDK/1.0.0'
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        self.logger.info("Trading client connected")
    
    async def disconnect(self):
        """Close HTTP session and cleanup"""
        if self.session:
            await self.session.close()
            self.session = None
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Trading client disconnected")
    
    @trace_async_function("trading.submit_order", "client")
    async def submit_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                          quantity: float, price: float = None, stop_price: float = None,
                          time_in_force: str = "day", idempotency_key: str = None) -> Order:
        """
        Submit order with idempotency protection
        
        Args:
            symbol: Trading symbol
            side: Buy or sell
            order_type: Order type
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force
            idempotency_key: Optional idempotency key for deduplication
            
        Returns:
            Submitted order
        """
        if not self.session:
            raise RuntimeError("Client not connected")
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = self.idempotency_manager.generate_idempotency_key()
        
        # Prepare request
        endpoint = "/api/v1/orders"
        method = "POST"
        payload = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": quantity,
            "time_in_force": time_in_force
        }
        
        if price is not None:
            payload["price"] = price
        if stop_price is not None:
            payload["stop_price"] = stop_price
        
        # Check idempotency
        cached_response = await self.idempotency_manager.check_and_store(
            idempotency_key, method, endpoint, payload
        )
        
        if cached_response:
            self.logger.info(f"Returning cached response for idempotency key {idempotency_key}")
            return self._deserialize_order(cached_response)
        
        # Execute request with circuit breaker
        @circuit_breaker(
            "trading_submit_order",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=15.0,
                max_retries=2,
                base_delay=0.5
            )
        )
        async def execute_request():
            async with self.semaphore:
                url = f"{self.base_url}{endpoint}"
                headers = {'Idempotency-Key': idempotency_key}
                
                async with self.session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
        
        try:
            response_data = await execute_request()
            
            # Store response for idempotency
            await self.idempotency_manager.store_response(idempotency_key, response_data)
            
            return self._deserialize_order(response_data)
            
        except Exception as e:
            self.logger.error(f"Order submission failed: {e}")
            raise
    
    @trace_async_function("trading.cancel_order", "client")
    async def cancel_order(self, order_id: str, idempotency_key: str = None) -> bool:
        """
        Cancel order with idempotency protection
        
        Args:
            order_id: Order ID to cancel
            idempotency_key: Optional idempotency key
            
        Returns:
            True if cancelled successfully
        """
        if not self.session:
            raise RuntimeError("Client not connected")
        
        if not idempotency_key:
            idempotency_key = self.idempotency_manager.generate_idempotency_key()
        
        endpoint = f"/api/v1/orders/{order_id}/cancel"
        method = "POST"
        payload = {}
        
        # Check idempotency
        cached_response = await self.idempotency_manager.check_and_store(
            idempotency_key, method, endpoint, payload
        )
        
        if cached_response:
            self.logger.info(f"Returning cached response for idempotency key {idempotency_key}")
            return cached_response.get("cancelled", False)
        
        @circuit_breaker(
            "trading_cancel_order",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=10.0,
                max_retries=2,
                base_delay=0.5
            )
        )
        async def execute_request():
            async with self.semaphore:
                url = f"{self.base_url}{endpoint}"
                headers = {'Idempotency-Key': idempotency_key}
                
                async with self.session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
        
        try:
            response_data = await execute_request()
            await self.idempotency_manager.store_response(idempotency_key, response_data)
            return response_data.get("cancelled", False)
            
        except Exception as e:
            self.logger.error(f"Order cancellation failed: {e}")
            raise
    
    @trace_async_function("trading.get_order", "client")
    async def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order details
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details or None if not found
        """
        if not self.session:
            raise RuntimeError("Client not connected")
        
        @circuit_breaker(
            "trading_get_order",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=10.0,
                max_retries=2,
                base_delay=0.5
            )
        )
        async def execute_request():
            async with self.semaphore:
                url = f"{self.base_url}/api/v1/orders/{order_id}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 404:
                        return None
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
        
        try:
            response_data = await execute_request()
            return self._deserialize_order(response_data) if response_data else None
            
        except Exception as e:
            self.logger.error(f"Get order failed: {e}")
            raise
    
    @trace_async_function("trading.get_positions", "client")
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions
        
        Returns:
            List of positions
        """
        if not self.session:
            raise RuntimeError("Client not connected")
        
        @circuit_breaker(
            "trading_get_positions",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=10.0,
                max_retries=2,
                base_delay=0.5
            )
        )
        async def execute_request():
            async with self.semaphore:
                url = f"{self.base_url}/api/v1/positions"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
        
        try:
            return await execute_request()
            
        except Exception as e:
            self.logger.error(f"Get positions failed: {e}")
            raise
    
    def _deserialize_order(self, data: Dict[str, Any]) -> Order:
        """Deserialize order from API response"""
        return Order(
            order_id=data["order_id"],
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            order_type=OrderType(data["type"]),
            quantity=float(data["quantity"]),
            price=float(data["price"]) if data.get("price") else None,
            stop_price=float(data["stop_price"]) if data.get("stop_price") else None,
            time_in_force=data["time_in_force"],
            status=OrderStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            filled_quantity=float(data.get("filled_quantity", 0)),
            average_price=float(data.get("average_price", 0)),
            fills=data.get("fills", [])
        )
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired records"""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean every hour
                await self.idempotency_manager.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "idempotency_cache": self.idempotency_manager.get_cache_stats(),
            "session_active": self.session is not None,
            "base_url": self.base_url
        }


# Convenience functions
def create_trading_client(base_url: str, api_key: str, 
                         idempotency_ttl_hours: int = 24) -> TradingClient:
    """Create a new trading client"""
    return TradingClient(base_url, api_key, idempotency_ttl_hours)
