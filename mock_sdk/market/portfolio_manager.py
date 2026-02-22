"""
Mock Portfolio Manager
Simulated portfolio management for demo purposes
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import random


class PortfolioManager:
    """Mock portfolio manager for demo purposes"""
    
    def __init__(self):
        """Initialize mock portfolio manager"""
        self.mock_portfolio = {
            "total_value": 1250000.00,
            "cash_balance": 125000.00,
            "positions": [
                {"symbol": "AAPL", "shares": 1000, "avg_cost": 175.50, "current_price": 182.52, "value": 182520.00, "unrealized_pnl": 7020.00},
                {"symbol": "GOOGL", "shares": 500, "avg_cost": 138.75, "current_price": 142.18, "value": 71090.00, "unrealized_pnl": 1715.00},
                {"symbol": "MSFT", "shares": 300, "avg_cost": 365.20, "current_price": 378.91, "value": 113673.00, "unrealized_pnl": 4113.00},
                {"symbol": "TSLA", "shares": 150, "avg_cost": 245.80, "current_price": 242.68, "value": 36402.00, "unrealized_pnl": -468.00}
            ],
            "performance": {
                "daily_return": 1.24,
                "weekly_return": 3.45,
                "monthly_return": 8.92,
                "year_to_date": 15.67,
                "sharpe_ratio": 1.85,
                "max_drawdown": -12.34,
                "volatility": 12.45
            }
        }
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Mock portfolio summary"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Add slight random variations to simulate real-time changes
        portfolio = self.mock_portfolio.copy()
        portfolio["total_value"] += random.uniform(-1000, 1000)
        portfolio["timestamp"] = datetime.now().isoformat()
        
        return portfolio
    
    async def get_position_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Mock position details"""
        await asyncio.sleep(0.05)
        
        symbol = symbol.upper()
        for position in self.mock_portfolio["positions"]:
            if position["symbol"] == symbol:
                return position
        return None
    
    async def execute_trade(self, symbol: str, side: str, quantity: int, price: Optional[float] = None) -> Dict[str, Any]:
        """Mock trade execution"""
        await asyncio.sleep(0.2)  # Simulate trade processing
        
        if price is None:
            # Use mock current price
            price = random.uniform(100, 300)
        
        trade_id = f"trade_{random.randint(10000, 99999)}"
        
        return {
            "trade_id": trade_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "value": quantity * price,
            "status": "filled",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_allocation_analysis(self) -> Dict[str, Any]:
        """Mock allocation analysis"""
        return {
            "allocation": {
                "equities": 65.5,
                "fixed_income": 20.0,
                "alternatives": 10.0,
                "cash": 4.5
            },
            "recommendations": [
                "Consider increasing equity allocation to 70%",
                "Fixed income allocation is appropriate for current market conditions",
                "Alternative investments provide good diversification"
            ],
            "risk_score": "Moderate",
            "optimization_potential": "High"
        }


def create_portfolio_manager():
    """Mock factory function for portfolio manager"""
    return PortfolioManager()
