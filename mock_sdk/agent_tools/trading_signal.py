"""
Mock Trading Signal Generator
Simulated trading signals for demo purposes
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import random


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradingSignal:
    """Mock trading signal generator for demo purposes"""
    
    def __init__(self):
        """Initialize mock trading signal generator"""
        self.signal_history = []
    
    def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock trading signal generation"""
        # Simple mock logic based on price change
        price_change = market_data.get("change", 0)
        
        if price_change > 2:
            signal_type = SignalType.BUY
            confidence = min(0.9, 0.5 + abs(price_change) / 10)
        elif price_change < -2:
            signal_type = SignalType.SELL
            confidence = min(0.9, 0.5 + abs(price_change) / 10)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.6
        
        signal = {
            "symbol": symbol,
            "signal_type": signal_type.value,
            "confidence": round(confidence, 2),
            "price": market_data.get("price", 0),
            "volume": market_data.get("volume", 0),
            "timestamp": datetime.now().isoformat(),
            "reasoning": self._generate_mock_reasoning(signal_type, price_change),
            "indicators": self._generate_mock_indicators()
        }
        
        self.signal_history.append(signal)
        return signal
    
    def _generate_mock_reasoning(self, signal_type: SignalType, price_change: float) -> str:
        """Generate mock reasoning for the signal"""
        reasoning_map = {
            SignalType.BUY: [
                "Strong upward momentum detected",
                "Breaking through resistance levels",
                "Positive volume divergence",
                "Oversold conditions with reversal patterns"
            ],
            SignalType.SELL: [
                "Bearish momentum confirmed",
                "Breaking support levels",
                "Negative volume divergence", 
                "Overbought conditions with reversal patterns"
            ],
            SignalType.HOLD: [
                "Sideways market conditions",
                "Waiting for clearer signals",
                "Consolidation phase detected",
                "Risk management: maintain current position"
            ]
        }
        
        return random.choice(reasoning_map.get(signal_type, ["Market analysis complete"]))
    
    def _generate_mock_indicators(self) -> Dict[str, Any]:
        """Generate mock technical indicators"""
        return {
            "rsi": round(random.uniform(20, 80), 2),
            "macd": round(random.uniform(-2, 2), 4),
            "bollinger_position": random.choice(["Lower", "Middle", "Upper"]),
            "volume_sma_ratio": round(random.uniform(0.5, 2.0), 2),
            "price_sma_20": round(random.uniform(100, 300), 2),
            "price_sma_50": round(random.uniform(90, 280), 2)
        }
    
    def get_signal_history(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get mock signal history"""
        history = self.signal_history
        if symbol:
            history = [s for s in history if s["symbol"] == symbol]
        return history[-limit:]
    
    def get_signal_performance(self) -> Dict[str, Any]:
        """Get mock signal performance metrics"""
        return {
            "total_signals": len(self.signal_history),
            "accuracy": round(random.uniform(0.65, 0.85), 3),
            "profitable_signals": int(len(self.signal_history) * random.uniform(0.6, 0.8)),
            "average_return": round(random.uniform(-2, 8), 2),
            "sharpe_ratio": round(random.uniform(0.8, 2.5), 2),
            "max_drawdown": round(random.uniform(-15, -5), 2)
        }
