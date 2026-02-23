# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Data Provider
# Licensing: Contact [Your Email]

"""
Market Data Provider Module
Real-time market data from multiple exchanges
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class Exchange(Enum):
    """Supported exchanges"""
    NYSE = "nyse"
    NASDAQ = "nasdaq"
    LSE = "lse"
    TSE = "tse"
    FX = "fx"


@dataclass
class MarketData:
    """Market data model"""
    symbol: str
    exchange: Exchange
    price: float
    bid: float
    ask: float
    volume: int
    change: float
    change_percent: float
    high: float
    low: float
    open_price: float
    previous_close: float
    timestamp: datetime
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None


@dataclass
class HistoricalData:
    """Historical market data"""
    symbol: str
    exchange: Exchange
    date: datetime
    open_price: float
    high: float
    low: float
    close_price: float
    volume: int
    adjusted_close: Optional[float] = None


class MarketDataProvider:
    """Enterprise market data provider"""
    
    def __init__(self, api_key: Optional[str] = None, cache_ttl_seconds: int = 60):
        """
        Initialize market data provider
        
        Args:
            api_key: API key for market data service
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.api_key = api_key
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_real_time_data(self, symbol: str, exchange: Exchange = Exchange.NYSE) -> MarketData:
        """
        Get real-time market data for a symbol
        
        Args:
            symbol: Stock symbol
            exchange: Exchange to query
            
        Returns:
            MarketData object
        """
        cache_key = f"{symbol}:{exchange.value}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        # Fetch fresh data
        data = await self._fetch_market_data(symbol, exchange)
        market_data = self._parse_market_data(data, symbol, exchange)
        
        # Update cache
        self.cache[cache_key] = {
            "data": market_data,
            "timestamp": datetime.now()
        }
        
        # Notify subscribers
        await self._notify_subscribers(symbol, market_data)
        
        return market_data
    
    async def get_historical_data(self, symbol: str, exchange: Exchange,
                                 start_date: datetime, end_date: datetime,
                                 interval: str = "1d") -> List[HistoricalData]:
        """
        Get historical market data
        
        Args:
            symbol: Stock symbol
            exchange: Exchange to query
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval (1d, 1h, 5m, etc.)
            
        Returns:
            List of HistoricalData objects
        """
        cache_key = f"{symbol}:{exchange.value}:hist:{start_date.date()}:{end_date.date()}:{interval}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        # Fetch historical data
        data = await self._fetch_historical_data(symbol, exchange, start_date, end_date, interval)
        historical_data = [self._parse_historical_data(item, symbol, exchange) for item in data]
        
        # Update cache
        self.cache[cache_key] = {
            "data": historical_data,
            "timestamp": datetime.now()
        }
        
        return historical_data
    
    async def subscribe_to_symbol(self, symbol: str, callback: Callable[[MarketData], None]):
        """
        Subscribe to real-time updates for a symbol
        
        Args:
            symbol: Stock symbol
            callback: Callback function for updates
        """
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        
        self.subscribers[symbol].append(callback)
        self.logger.info(f"Subscribed to updates for {symbol}")
    
    async def unsubscribe_from_symbol(self, symbol: str, callback: Callable[[MarketData], None]):
        """
        Unsubscribe from real-time updates for a symbol
        
        Args:
            symbol: Stock symbol
            callback: Callback function to remove
        """
        if symbol in self.subscribers:
            try:
                self.subscribers[symbol].remove(callback)
                self.logger.info(f"Unsubscribed from updates for {symbol}")
            except ValueError:
                pass
    
    async def get_market_summary(self, exchange: Exchange = Exchange.NYSE) -> Dict[str, Any]:
        """
        Get market summary for an exchange
        
        Args:
            exchange: Exchange to query
            
        Returns:
            Market summary data
        """
        # Mock implementation for demo
        return {
            "exchange": exchange.value,
            "status": "open",
            "indices": {
                "S&P 500": {"price": 4500.25, "change": 15.75, "change_percent": 0.35},
                "DOW": {"price": 35000.00, "change": 125.50, "change_percent": 0.36},
                "NASDAQ": {"price": 14000.00, "change": 85.25, "change_percent": 0.61}
            },
            "volume": 1250000000,
            "advancers": 1850,
            "decliners": 1150,
            "timestamp": datetime.now().isoformat()
        }
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols by name or ticker
        
        Args:
            query: Search query
            
        Returns:
            List of matching symbols
        """
        # Mock implementation for demo
        mock_symbols = [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "sector": "Technology"},
        ]
        
        results = []
        query_lower = query.lower()
        
        for symbol in mock_symbols:
            if (query_lower in symbol["symbol"].lower() or 
                query_lower in symbol["name"].lower()):
                results.append(symbol)
        
        return results
    
    async def _fetch_market_data(self, symbol: str, exchange: Exchange) -> Dict[str, Any]:
        """Fetch market data from API"""
        # Mock implementation for demo
        await asyncio.sleep(0.1)  # Simulate API call
        
        base_price = 100.0 + hash(symbol) % 500
        change = (hash(symbol + "change") % 20 - 10) / 10
        
        return {
            "symbol": symbol,
            "price": base_price + change,
            "bid": base_price + change - 0.01,
            "ask": base_price + change + 0.01,
            "volume": hash(symbol + "vol") % 10000000 + 1000000,
            "change": change,
            "change_percent": (change / base_price) * 100,
            "high": base_price + abs(change) + 2,
            "low": base_price - abs(change) - 2,
            "open": base_price,
            "previous_close": base_price,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fetch_historical_data(self, symbol: str, exchange: Exchange,
                                   start_date: datetime, end_date: datetime,
                                   interval: str) -> List[Dict[str, Any]]:
        """Fetch historical data from API"""
        # Mock implementation for demo
        await asyncio.sleep(0.2)  # Simulate API call
        
        days = (end_date - start_date).days
        base_price = 100.0 + hash(symbol) % 500
        
        data = []
        current_date = start_date
        current_price = base_price
        
        for i in range(min(days, 365)):  # Limit to 1 year
            change = (hash(symbol + str(i)) % 10 - 5) / 10
            current_price += change
            
            data.append({
                "date": current_date.isoformat(),
                "open": current_price - 0.5,
                "high": current_price + abs(change) + 1,
                "low": current_price - abs(change) - 1,
                "close": current_price,
                "volume": hash(symbol + str(i)) % 1000000 + 100000
            })
            
            current_date += timedelta(days=1)
        
        return data
    
    def _parse_market_data(self, data: Dict[str, Any], symbol: str, exchange: Exchange) -> MarketData:
        """Parse market data from API response"""
        return MarketData(
            symbol=symbol,
            exchange=exchange,
            price=data["price"],
            bid=data["bid"],
            ask=data["ask"],
            volume=data["volume"],
            change=data["change"],
            change_percent=data["change_percent"],
            high=data["high"],
            low=data["low"],
            open_price=data["open"],
            previous_close=data["previous_close"],
            timestamp=datetime.now()
        )
    
    def _parse_historical_data(self, data: Dict[str, Any], symbol: str, exchange: Exchange) -> HistoricalData:
        """Parse historical data from API response"""
        return HistoricalData(
            symbol=symbol,
            exchange=exchange,
            date=datetime.fromisoformat(data["date"]),
            open_price=data["open"],
            high=data["high"],
            low=data["low"],
            close_price=data["close"],
            volume=data["volume"]
        )
    
    async def _notify_subscribers(self, symbol: str, data: MarketData):
        """Notify subscribers of new data"""
        if symbol in self.subscribers:
            for callback in self.subscribers[symbol]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback: {e}")


def create_market_data_provider(api_key: Optional[str] = None, cache_ttl_seconds: int = 60) -> MarketDataProvider:
    """Create a new market data provider"""
    return MarketDataProvider(api_key, cache_ttl_seconds)
