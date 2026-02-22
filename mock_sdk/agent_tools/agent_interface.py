"""
Mock Agent Interface
Simulated AI agent interface for demo purposes
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random


class AgentInterface:
    """Mock AI agent interface for demo purposes"""
    
    def __init__(self):
        """Initialize mock agent interface"""
        self.conversation_history = []
        self.agent_capabilities = [
            "market_analysis",
            "portfolio_optimization", 
            "risk_assessment",
            "trading_signals",
            "compliance_monitoring"
        ]
    
    async def process_request(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock AI request processing"""
        await asyncio.sleep(1)  # Simulate AI processing time
        
        # Generate mock response based on prompt keywords
        response_type = self._classify_request(user_prompt)
        response = self._generate_mock_response(response_type, user_prompt)
        
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "agent_response": response,
            "context": context or {},
            "response_type": response_type,
            "confidence": round(random.uniform(0.75, 0.95), 2)
        }
        
        self.conversation_history.append(conversation_entry)
        
        return {
            "response": response,
            "response_type": response_type,
            "confidence": conversation_entry["confidence"],
            "timestamp": conversation_entry["timestamp"],
            "processing_time": "1.2s"
        }
    
    def _classify_request(self, prompt: str) -> str:
        """Classify the type of request"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["market", "stock", "price", "symbol"]):
            return "market_analysis"
        elif any(word in prompt_lower for word in ["portfolio", "allocation", "diversify"]):
            return "portfolio_optimization"
        elif any(word in prompt_lower for word in ["risk", "volatility", "drawdown"]):
            return "risk_assessment"
        elif any(word in prompt_lower for word in ["buy", "sell", "trade", "signal"]):
            return "trading_signals"
        elif any(word in prompt_lower for word in ["compliance", "audit", "security"]):
            return "compliance_monitoring"
        else:
            return "general_inquiry"
    
    def _generate_mock_response(self, response_type: str, prompt: str) -> Dict[str, Any]:
        """Generate mock response based on type"""
        responses = {
            "market_analysis": {
                "analysis": "Based on current market conditions, we're seeing mixed signals across major indices. Tech stocks show resilience while energy sectors face headwinds.",
                "recommendations": ["Consider defensive positioning", "Monitor interest rate developments", "Review sector allocation"],
                "data_points": {
                    "market_sentiment": random.choice(["Bullish", "Bearish", "Neutral"]),
                    "volatility_index": round(random.uniform(15, 35), 2),
                    "sector_performance": {
                        "Technology": f"+{random.uniform(1, 5):.2f}%",
                        "Healthcare": f"+{random.uniform(0.5, 3):.2f}%",
                        "Finance": f"{random.uniform(-2, 2):.2f}%"
                    }
                }
            },
            "portfolio_optimization": {
                "analysis": "Your current portfolio shows good diversification but could benefit from rebalancing. The allocation model suggests adjusting equity exposure.",
                "recommendations": [
                    "Increase international equity allocation to 15%",
                    "Reduce domestic large-cap to 45%",
                    "Add 5% allocation to emerging markets"
                ],
                "optimization_metrics": {
                    "expected_return": f"{random.uniform(6, 12):.2f}%",
                    "risk_score": random.choice(["Low", "Medium", "High"]),
                    "sharpe_ratio": round(random.uniform(0.8, 2.0), 2)
                }
            },
            "risk_assessment": {
                "analysis": "Portfolio risk levels are within acceptable parameters. Value at Risk (VaR) calculations show moderate downside potential.",
                "risk_metrics": {
                    "var_95": f"${random.uniform(50000, 150000):.0f}",
                    "max_drawdown": f"{random.uniform(-15, -5):.2f}%",
                    "beta": round(random.uniform(0.8, 1.3), 2),
                    "correlation_to_market": round(random.uniform(0.6, 0.95), 2)
                },
                "recommendations": [
                    "Consider adding hedges for downside protection",
                    "Monitor concentration risk in top holdings",
                    "Review stop-loss levels"
                ]
            },
            "trading_signals": {
                "analysis": "Current market conditions generate several trading opportunities across different timeframes.",
                "signals": [
                    {"symbol": "AAPL", "action": "BUY", "confidence": 0.82, "reasoning": "Strong momentum with positive volume divergence"},
                    {"symbol": "TSLA", "action": "HOLD", "confidence": 0.65, "reasoning": "Consolidation phase, wait for breakout"},
                    {"symbol": "MSFT", "action": "BUY", "confidence": 0.78, "reasoning": "Breaking through resistance levels"}
                ],
                "market_outlook": random.choice(["Bullish", "Bearish", "Neutral"])
            },
            "compliance_monitoring": {
                "analysis": "All compliance checks passed. Recent activities are within regulatory guidelines.",
                "compliance_status": "COMPLIANT",
                "alerts": [],
                "last_audit": datetime.now().isoformat(),
                "recommendations": [
                    "Continue regular monitoring",
                    "Update documentation as needed",
                    "Schedule next compliance review"
                ]
            },
            "general_inquiry": {
                "analysis": f"I understand you're asking about: {prompt}. Let me provide you with relevant information based on current market data and portfolio analysis.",
                "recommendations": [
                    "Review your investment objectives",
                    "Consider current market conditions",
                    "Consult with financial advisor if needed"
                ]
            }
        }
        
        return responses.get(response_type, responses["general_inquiry"])
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history[-limit:]
    
    def get_agent_capabilities(self) -> List[str]:
        """Get list of agent capabilities"""
        return self.agent_capabilities
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get mock agent performance metrics"""
        return {
            "total_requests": len(self.conversation_history),
            "average_response_time": "1.2s",
            "success_rate": "99.2%",
            "user_satisfaction": round(random.uniform(4.2, 4.8), 1),
            "most_used_features": [
                {"feature": "market_analysis", "usage_count": 45},
                {"feature": "portfolio_optimization", "usage_count": 32},
                {"feature": "trading_signals", "usage_count": 28}
            ]
        }
