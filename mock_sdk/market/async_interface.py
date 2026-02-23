# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Async Interface
# Licensing: Contact [Your Email]

"""
Async Market Interface Module
High-performance async interface for market operations
"""

import asyncio
import aiohttp
import websockets
import json
from typing import Dict, Any, Optional, List, Callable, AsyncIterator
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from ..network_utils import circuit_breaker, CircuitBreakerConfig
from ..observability import trace_async_function
from .data_provider import MarketData, Exchange


class ConnectionStatus(Enum):
    """WebSocket connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class StreamMessage:
    """WebSocket stream message"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    sequence: int


class AsyncMarketInterface:
    """High-performance async market interface"""
    
    def __init__(self, ws_url: str = "wss://stream.marketdata.com", 
                 api_key: Optional[str] = None,
                 max_connections: int = 10):
        """
        Initialize async market interface
        
        Args:
            ws_url: WebSocket URL for streaming data
            api_key: API key for authentication
            max_connections: Maximum concurrent connections
        """
        self.ws_url = ws_url
        self.api_key = api_key
        self.max_connections = max_connections
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_connections)
        self.message_queue = asyncio.Queue()
        self.sequence_counter = 0
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    @trace_async_function("market.connect", "client")
    async def connect(self):
        """Connect to WebSocket stream"""
        if self.connection_status == ConnectionStatus.CONNECTED:
            return
        
        self.connection_status = ConnectionStatus.CONNECTING
        
        try:
            # Create HTTP session for REST API calls
            self.session = aiohttp.ClientSession()
            
            # Connect to WebSocket
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self.websocket = await websockets.connect(self.ws_url, extra_headers=headers)
            self.connection_status = ConnectionStatus.CONNECTED
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
            self.logger.info("Connected to market data stream")
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket stream"""
        self.connection_status = ConnectionStatus.DISCONNECTED
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        self.logger.info("Disconnected from market data stream")
    
    async def subscribe_to_stream(self, symbols: List[str], 
                                 data_types: List[str] = ["quote", "trade"]) -> bool:
        """
        Subscribe to real-time data stream
        
        Args:
            symbols: List of symbols to subscribe to
            data_types: Types of data to receive
            
        Returns:
            True if subscription successful
        """
        if self.connection_status != ConnectionStatus.CONNECTED:
            raise RuntimeError("Not connected to market data stream")
        
        subscription_msg = {
            "action": "subscribe",
            "symbols": symbols,
            "types": data_types,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(subscription_msg))
        
        # Wait for confirmation
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        return response_data.get("status") == "subscribed"
    
    async def unsubscribe_from_stream(self, symbols: List[str]) -> bool:
        """
        Unsubscribe from real-time data stream
        
        Args:
            symbols: List of symbols to unsubscribe from
            
        Returns:
            True if unsubscription successful
        """
        if self.connection_status != ConnectionStatus.CONNECTED:
            return False
        
        unsubscription_msg = {
            "action": "unsubscribe",
            "symbols": symbols,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(unsubscription_msg))
        
        # Wait for confirmation
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        return response_data.get("status") == "unsubscribed"
    
    async def get_batch_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """
        Get market data for multiple symbols concurrently
        
        Args:
            symbols: List of symbols to fetch
            
        Returns:
            Dictionary of symbol -> MarketData
        """
        if not self.session:
            raise RuntimeError("HTTP session not initialized")
        
        @circuit_breaker(
            "market_data_batch",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=10.0,
                max_retries=2,
                base_delay=0.5
            )
        )
        async def fetch_symbol_data(symbol: str) -> tuple[str, Optional[MarketData]]:
            async with self.semaphore:
                try:
                    # Mock API call for demo
                    await asyncio.sleep(0.1)
                    
                    # Generate mock data
                    base_price = 100.0 + hash(symbol) % 500
                    change = (hash(symbol + "change") % 20 - 10) / 10
                    
                    market_data = MarketData(
                        symbol=symbol,
                        exchange=Exchange.NYSE,
                        price=base_price + change,
                        bid=base_price + change - 0.01,
                        ask=base_price + change + 0.01,
                        volume=hash(symbol + "vol") % 10000000 + 1000000,
                        change=change,
                        change_percent=(change / base_price) * 100,
                        high=base_price + abs(change) + 2,
                        low=base_price - abs(change) - 2,
                        open_price=base_price,
                        previous_close=base_price,
                        timestamp=datetime.now()
                    )
                    
                    return symbol, market_data
                    
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {e}")
                    return symbol, None
        
        # Fetch all symbols concurrently
        tasks = [fetch_symbol_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        # Convert results to dictionary
        market_data_dict = {}
        for symbol, data in results:
            if data:
                market_data_dict[symbol] = data
        
        return market_data_dict
    
    async def stream_market_data(self, symbols: List[str]) -> AsyncIterator[StreamMessage]:
        """
        Stream market data for symbols
        
        Args:
            symbols: List of symbols to stream
            
        Yields:
            StreamMessage objects
        """
        if self.connection_status != ConnectionStatus.CONNECTED:
            raise RuntimeError("Not connected to market data stream")
        
        # Subscribe to symbols
        await self.subscribe_to_stream(symbols)
        
        try:
            while self.connection_status == ConnectionStatus.CONNECTED:
                # Get message from queue
                message = await self.message_queue.get()
                
                # Filter for subscribed symbols
                if message.data.get("symbol") in symbols:
                    yield message
                    
        finally:
            # Unsubscribe when done
            await self.unsubscribe_from_stream(symbols)
    
    async def execute_batch_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple orders concurrently
        
        Args:
            orders: List of order dictionaries
            
        Returns:
            List of order results
        """
        if not self.session:
            raise RuntimeError("HTTP session not initialized")
        
        async def execute_order(order: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    # Mock order execution
                    await asyncio.sleep(0.05)
                    
                    return {
                        "order_id": f"order_{datetime.now().timestamp()}_{hash(str(order)) % 10000}",
                        "symbol": order["symbol"],
                        "side": order["side"],
                        "quantity": order["quantity"],
                        "price": order.get("price", "market"),
                        "status": "filled",
                        "filled_quantity": order["quantity"],
                        "average_price": 100.0 + hash(order["symbol"]) % 500,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    return {
                        "order_id": None,
                        "symbol": order["symbol"],
                        "error": str(e),
                        "status": "rejected",
                        "timestamp": datetime.now().isoformat()
                    }
        
        # Execute all orders concurrently
        tasks = [execute_order(order) for order in orders]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def get_market_depth(self, symbol: str, levels: int = 10) -> Dict[str, Any]:
        """
        Get market order book depth
        
        Args:
            symbol: Stock symbol
            levels: Number of price levels
            
        Returns:
            Order book data
        """
        if not self.session:
            raise RuntimeError("HTTP session not initialized")
        
        # Mock order book data
        base_price = 100.0 + hash(symbol) % 500
        
        bids = []
        asks = []
        
        for i in range(levels):
            bid_price = base_price - (i + 1) * 0.01
            ask_price = base_price + (i + 1) * 0.01
            
            bids.append({
                "price": bid_price,
                "quantity": (hash(symbol + f"bid{i}") % 10000) + 100,
                "orders": (hash(symbol + f"bid_orders{i}") % 50) + 1
            })
            
            asks.append({
                "price": ask_price,
                "quantity": (hash(symbol + f"ask{i}") % 10000) + 100,
                "orders": (hash(symbol + f"ask_orders{i}") % 50) + 1
            })
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "bids": bids,
            "asks": asks,
            "spread": asks[0]["price"] - bids[0]["price"],
            "spread_percent": ((asks[0]["price"] - bids[0]["price"]) / base_price) * 100
        }
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # Create stream message
                    stream_msg = StreamMessage(
                        type=data.get("type", "unknown"),
                        data=data,
                        timestamp=datetime.now(),
                        sequence=self.sequence_counter
                    )
                    
                    self.sequence_counter += 1
                    
                    # Add to queue
                    await self.message_queue.put(stream_msg)
                    
                    # Notify subscribers
                    await self._notify_subscribers(stream_msg)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.connection_status = ConnectionStatus.DISCONNECTED
            self.logger.warning("WebSocket connection closed")
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"WebSocket error: {e}")
    
    async def _notify_subscribers(self, message: StreamMessage):
        """Notify subscribers of new messages"""
        message_type = message.type
        
        if message_type in self.subscribers:
            for callback in self.subscribers[message_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback: {e}")
    
    def subscribe_to_messages(self, message_type: str, callback: Callable[[StreamMessage], None]):
        """Subscribe to specific message types"""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        
        self.subscribers[message_type].append(callback)
    
    def unsubscribe_from_messages(self, message_type: str, callback: Callable[[StreamMessage], None]):
        """Unsubscribe from specific message types"""
        if message_type in self.subscribers:
            try:
                self.subscribers[message_type].remove(callback)
            except ValueError:
                pass
