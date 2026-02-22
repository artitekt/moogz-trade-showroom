"""
Mock Async Market Interface
Simulated async interface for demo purposes
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime


class AsyncMarketInterface:
    """Mock async market interface for demo purposes"""
    
    def __init__(self):
        """Initialize mock async market interface"""
        self.connected = False
        self.subscriptions = {}
    
    async def connect(self) -> bool:
        """Mock connection to market data feed"""
        await asyncio.sleep(0.5)  # Simulate connection time
        self.connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Mock disconnection from market data feed"""
        await asyncio.sleep(0.1)
        self.connected = False
        self.subscriptions.clear()
        return True
    
    async def subscribe(self, symbol: str, callback) -> bool:
        """Mock subscription to real-time data"""
        if not self.connected:
            return False
        
        await asyncio.sleep(0.1)
        self.subscriptions[symbol] = callback
        return True
    
    async def unsubscribe(self, symbol: str) -> bool:
        """Mock unsubscription from real-time data"""
        await asyncio.sleep(0.05)
        if symbol in self.subscriptions:
            del self.subscriptions[symbol]
            return True
        return False
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Mock market status"""
        return {
            "market_open": True,
            "next_open": datetime.now().replace(hour=9, minute=30).isoformat(),
            "next_close": datetime.now().replace(hour=16, minute=0).isoformat(),
            "timezone": "EST",
            "exchange": "NYSE"
        }
    
    async def get_trading_calendar(self, days: int = 30) -> List[Dict[str, Any]]:
        """Mock trading calendar"""
        import random
        calendar = []
        
        for i in range(days):
            is_trading_day = random.choice([True, True, True, False])  # 75% trading days
            calendar.append({
                "date": f"2024-01-{i+1:02d}",
                "is_trading_day": is_trading_day,
                "market_open": "09:30" if is_trading_day else None,
                "market_close": "16:00" if is_trading_day else None
            })
        
        return calendar
