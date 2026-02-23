# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Schemas
# Licensing: Contact [Your Email]

"""
Pydantic Schemas Module
Data models for AI trading agents
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json


class SignalType(str, Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class TimeInForce(str, Enum):
    """Time in force options"""
    DAY = "day"
    GTC = "gtc"  # Good till cancelled
    IOC = "ioc"   # Immediate or cancel
    FOK = "fok"   # Fill or kill


class RiskLevel(str, Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TradingSignal(BaseModel):
    """Trading signal schema"""
    symbol: str = Field(..., description="Stock symbol")
    signal_type: SignalType = Field(..., description="Type of trading signal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    time_horizon: str = Field(..., description="Investment time horizon")
    reasoning: str = Field(..., description="AI reasoning for the signal")
    indicators: Dict[str, float] = Field(default_factory=dict, description="Technical indicators")
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None, description="Signal expiry time")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v


class OrderRequest(BaseModel):
    """Order request schema"""
    symbol: str = Field(..., description="Stock symbol")
    order_type: OrderType = Field(..., description="Type of order")
    side: str = Field(..., description="Buy or sell")
    quantity: float = Field(..., gt=0, description="Number of shares")
    price: Optional[float] = Field(None, description="Order price (for limit orders)")
    stop_price: Optional[float] = Field(None, description="Stop price (for stop orders)")
    time_in_force: TimeInForce = Field(TimeInForce.DAY, description="Time in force")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be either buy or sell')
        return v.lower()


class PortfolioAllocation(BaseModel):
    """Portfolio allocation schema"""
    total_value: float = Field(..., gt=0, description="Total portfolio value")
    cash_allocation: float = Field(..., ge=0, description="Cash allocation amount")
    allocations: Dict[str, float] = Field(..., description="Asset allocations by sector/class")
    risk_tolerance: RiskLevel = Field(..., description="Risk tolerance level")
    rebalance_threshold: float = Field(0.05, ge=0, le=1, description="Rebalancing threshold")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('allocations')
    @classmethod
    def validate_allocations(cls, v):
        total_allocation = sum(v.values())
        if total_allocation > 1.0:
            raise ValueError('Total allocation cannot exceed 100%')
        return v


class RiskAssessment(BaseModel):
    """Risk assessment schema"""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    overall_risk: RiskLevel = Field(..., description="Overall risk level")
    var_95: float = Field(..., description="Value at Risk (95% confidence)")
    var_99: float = Field(..., description="Value at Risk (99% confidence)")
    beta: float = Field(..., description="Portfolio beta")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    volatility: float = Field(..., ge=0, description="Portfolio volatility")
    concentration_risk: Dict[str, float] = Field(default_factory=dict, description="Concentration risk by sector")
    liquidity_risk: float = Field(ge=0, description="Liquidity risk score")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('volatility')
    @classmethod
    def validate_volatility(cls, v):
        if v < 0:
            raise ValueError('Volatility cannot be negative')
        return v


class MarketAnalysis(BaseModel):
    """Market analysis schema"""
    analysis_type: str = Field(..., description="Type of analysis (technical, fundamental, sentiment)")
    symbol: str = Field(..., description="Stock symbol")
    timeframe: str = Field(..., description="Analysis timeframe")
    overall_sentiment: str = Field(..., description="Overall market sentiment")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Key analysis metrics")
    support_levels: List[float] = Field(default_factory=list, description="Support levels")
    resistance_levels: List[float] = Field(default_factory=list, description="Resistance levels")
    trend_analysis: Dict[str, str] = Field(default_factory=dict, description="Trend analysis")
    recommendations: List[TradingSignal] = Field(default_factory=list, description="Trading recommendations")
    confidence_score: float = Field(..., ge=0, le=1, description="Analysis confidence score")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v


class AgentConfig(BaseModel):
    """AI agent configuration schema"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: str = Field(..., description="Human-readable agent name")
    agent_type: str = Field(..., description="Type of AI agent")
    ai_model_config: Dict[str, Any] = Field(default_factory=dict, description="Model configuration")
    trading_parameters: Dict[str, Any] = Field(default_factory=dict, description="Trading parameters")
    risk_limits: Dict[str, float] = Field(default_factory=dict, description="Risk limits")
    allowed_operations: List[str] = Field(default_factory=list, description="Allowed operations")
    api_permissions: List[str] = Field(default_factory=list, description="API permissions")
    is_active: bool = Field(True, description="Whether agent is active")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class AgentExecution(BaseModel):
    """Agent execution record schema"""
    execution_id: str = Field(..., description="Unique execution identifier")
    agent_id: str = Field(..., description="Agent identifier")
    task_type: str = Field(..., description="Type of task executed")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for execution")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output data from execution")
    execution_time: float = Field(..., description="Execution time in seconds")
    success: bool = Field(..., description="Whether execution was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.now)


class Alert(BaseModel):
    """Alert schema"""
    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: RiskLevel = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    symbol: Optional[str] = Field(None, description="Related symbol")
    portfolio_id: Optional[str] = Field(None, description="Related portfolio")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    is_acknowledged: bool = Field(False, description="Whether alert has been acknowledged")
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")


class PerformanceMetrics(BaseModel):
    """Performance metrics schema"""
    period_start: datetime = Field(..., description="Start of measurement period")
    period_end: datetime = Field(..., description="End of measurement period")
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    volatility: float = Field(..., ge=0, description="Volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate")
    profit_factor: float = Field(..., description="Profit factor")
    average_win: float = Field(..., description="Average win amount")
    average_loss: float = Field(..., description="Average loss amount")
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    winning_trades: int = Field(..., ge=0, description="Number of winning trades")


class BacktestResult(BaseModel):
    """Backtest result schema"""
    backtest_id: str = Field(..., description="Unique backtest identifier")
    strategy_name: str = Field(..., description="Strategy name")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., gt=0, description="Initial capital")
    final_capital: float = Field(..., gt=0, description="Final capital")
    total_return: float = Field(..., description="Total return percentage")
    performance_metrics: PerformanceMetrics = Field(..., description="Detailed performance metrics")
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="List of trades")
    daily_returns: List[float] = Field(default_factory=list, description="Daily returns")
    benchmark_return: Optional[float] = Field(None, description="Benchmark return")
    created_at: datetime = Field(default_factory=datetime.now)


# Utility functions for schema validation
def validate_trading_signal(data: Dict[str, Any]) -> TradingSignal:
    """Validate and create TradingSignal from dictionary"""
    return TradingSignal(**data)


def validate_order_request(data: Dict[str, Any]) -> OrderRequest:
    """Validate and create OrderRequest from dictionary"""
    return OrderRequest(**data)


def validate_portfolio_allocation(data: Dict[str, Any]) -> PortfolioAllocation:
    """Validate and create PortfolioAllocation from dictionary"""
    return PortfolioAllocation(**data)


def validate_risk_assessment(data: Dict[str, Any]) -> RiskAssessment:
    """Validate and create RiskAssessment from dictionary"""
    return RiskAssessment(**data)


def validate_market_analysis(data: Dict[str, Any]) -> MarketAnalysis:
    """Validate and create MarketAnalysis from dictionary"""
    return MarketAnalysis(**data)


# Schema export utilities
def schema_to_json(schema: BaseModel) -> str:
    """Convert Pydantic schema to JSON string"""
    return schema.json()


def schema_to_dict(schema: BaseModel) -> Dict[str, Any]:
    """Convert Pydantic schema to dictionary"""
    return schema.dict()


def load_schema_from_json(json_str: str, schema_class: type) -> BaseModel:
    """Load Pydantic schema from JSON string"""
    return schema_class.parse_raw(json_str)
