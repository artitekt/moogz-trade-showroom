"""
Mock Market Data Provider
Simulated market data for demo purposes
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from enum import Enum


class Exchange(Enum):
    """Mock exchange enumeration"""
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    LSE = "LSE"
    CRYPTO = "CRYPTO"


class MarketDataProvider:
    """Mock market data provider for demo purposes"""
    
    def __init__(self):
        """Initialize mock market data provider"""
        self.mock_data = {
            "AAPL": {"price": 182.52, "change": 2.34, "volume": 45678901, "exchange": "NASDAQ"},
            "GOOGL": {"price": 142.18, "change": -0.89, "volume": 23456789, "exchange": "NASDAQ"},
            "MSFT": {"price": 378.91, "change": 4.12, "volume": 34567890, "exchange": "NASDAQ"},
            "TSLA": {"price": 242.68, "change": -3.21, "volume": 56789012, "exchange": "NASDAQ"},
            "AMZN": {"price": 178.35, "change": 1.87, "volume": 28345678, "exchange": "NASDAQ"}
        }
    
    async def get_real_time_data(self, symbol: str, exchange: Exchange) -> Dict[str, Any]:
        """Mock real-time market data"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        symbol = symbol.upper()
        if symbol in self.mock_data:
            data = self.mock_data[symbol].copy()
            # Add slight random variation to simulate real-time changes
            import random
            data["price"] += random.uniform(-0.5, 0.5)
            data["timestamp"] = datetime.now().isoformat()
            return data
        else:
            # Generate mock data for unknown symbols
            return {
                "price": round(random.uniform(50, 500), 2),
                "change": round(random.uniform(-5, 5), 2),
                "volume": random.randint(1000000, 50000000),
                "exchange": exchange.value,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Mock historical data"""
        import random
        historical_data = []
        base_price = random.uniform(100, 300)
        
        for i in range(days):
            price = base_price + random.uniform(-10, 10)
            historical_data.append({
                "date": f"2024-01-{i+1:02d}",
                "open": price,
                "high": price + random.uniform(0, 5),
                "low": price - random.uniform(0, 5),
                "close": price + random.uniform(-2, 2),
                "volume": random.randint(1000000, 10000000)
            })
        
        return historical_data


def create_market_data_provider():
    """Mock factory function for market data provider"""
    return MarketDataProvider()
