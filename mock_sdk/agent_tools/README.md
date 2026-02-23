# MoogzTrade Agent Tools Module

Pydantic schemas and audit logging for AI trading agents.

## Overview

The Agent Tools Module provides comprehensive data validation, audit logging, and interface components specifically designed for AI-powered trading systems. Ensure your AI agents operate with proper governance, compliance, and traceability.

## Features

### 📋 Pydantic Schemas
- Type-safe data models for trading operations
- Automatic validation and serialization
- Comprehensive trading signal schemas
- Portfolio and risk assessment models
- Order and execution tracking

### 📊 Audit Logging
- Comprehensive audit trail for all agent operations
- Security event logging
- Performance tracking and analytics
- Regulatory compliance support
- Real-time monitoring capabilities

### 🤖 Agent Interface
- High-level AI agent management
- Task scheduling and execution
- Async operation support
- Performance metrics and monitoring
- Error handling and recovery

## Installation

```bash
pip install moogztrade-agent-tools
```

## Quick Start

### Trading Signals with Validation

```python
from moogztrade_agent_tools import TradingSignal, SignalType
from datetime import datetime, timedelta

# Create validated trading signal
signal = TradingSignal(
    symbol="AAPL",
    signal_type=SignalType.BUY,
    confidence=0.85,
    target_price=185.50,
    stop_loss=175.00,
    time_horizon="1M",
    reasoning="Strong technical indicators with volume confirmation",
    indicators={"rsi": 65.2, "macd": 1.8, "volume_ratio": 1.5},
    expires_at=datetime.now() + timedelta(hours=24)
)

print(f"Signal: {signal.signal_type.value} {signal.symbol}")
print(f"Confidence: {signal.confidence:.2%}")
print(f"Target: ${signal.target_price}")
```

### Order Management

```python
from moogztrade_agent_tools import OrderRequest, OrderType, TimeInForce

# Create validated order request
order = OrderRequest(
    symbol="AAPL",
    order_type=OrderType.LIMIT,
    side="buy",
    quantity=100,
    price=182.50,
    time_in_force=TimeInForce.DAY
)

print(f"Order: {order.side.upper()} {order.quantity} {order.symbol} @ ${order.price}")
```

### Portfolio Allocation

```python
from moogztrade_agent_tools import PortfolioAllocation, RiskLevel

# Create portfolio allocation
allocation = PortfolioAllocation(
    total_value=1000000,
    cash_allocation=50000,
    allocations={
        "Technology": 0.40,
        "Healthcare": 0.25,
        "Finance": 0.20,
        "Consumer Goods": 0.15
    },
    risk_tolerance=RiskLevel.MODERATE,
    rebalance_threshold=0.05
)

print(f"Portfolio Value: ${allocation.total_value:,.2f}")
print(f"Cash: ${allocation.cash_allocation:,.2f}")
print(f"Risk Level: {allocation.risk_tolerance.value}")
```

### Risk Assessment

```python
from moogztrade_agent_tools import RiskAssessment, RiskLevel

# Create risk assessment
risk = RiskAssessment(
    portfolio_id="portfolio_123",
    overall_risk=RiskLevel.MEDIUM,
    var_95=25000,  # 95% VaR
    var_99=35000,  # 99% VaR
    beta=1.15,
    sharpe_ratio=1.85,
    max_drawdown=-0.12,
    volatility=0.18,
    concentration_risk={
        "Technology": 0.45,
        "Healthcare": 0.25,
        "Finance": 0.30
    },
    liquidity_risk=0.3
)

print(f"Portfolio Risk: {risk.overall_risk.value}")
print(f"95% VaR: ${risk.var_95:,.2f}")
print(f"Sharpe Ratio: {risk.sharpe_ratio:.2f}")
```

### Audit Logging

```python
import asyncio
from moogztrade_agent_tools import AuditLogger, AuditEventType, SeverityLevel

async def audit_demo():
    # Initialize audit logger
    logger = AuditLogger(log_file="trading_audit.log")
    
    # Log trading signal generation
    await logger.log_signal_generated(
        agent_id="ai_trader_001",
        symbol="AAPL",
        signal_type="BUY",
        confidence=0.85,
        reasoning="Technical analysis indicates bullish momentum"
    )
    
    # Log order execution
    await logger.log_order_event(
        event_type=AuditEventType.ORDER_FILLED,
        order_id="order_12345",
        symbol="AAPL",
        side="buy",
        quantity=100,
        price=182.50,
        agent_id="ai_trader_001"
    )
    
    # Log risk assessment
    await logger.log_risk_assessment(
        portfolio_id="portfolio_123",
        risk_score=0.65,
        risk_factors={"beta": 1.15, "volatility": 0.18},
        agent_id="ai_trader_001"
    )
    
    print("Audit events logged successfully")

asyncio.run(audit_demo())
```

### AI Agent Interface

```python
import asyncio
from moogztrade_agent_tools import (
    AgentInterface, AgentConfig, AuditLogger,
    create_agent_interface
)

async def agent_demo():
    # Create audit logger
    audit_logger = AuditLogger()
    
    # Configure AI agent
    config = AgentConfig(
        agent_id="ai_trader_001",
        agent_name="Momentum Trader",
        agent_type="momentum_strategy",
        model_config={
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 1000
        },
        trading_parameters={
            "max_position_size": 100000,
            "risk_limit": 0.02,
            "confidence_threshold": 0.8
        },
        risk_limits={
            "max_drawdown": 0.15,
            "var_limit": 0.05
        },
        allowed_operations=[
            "generate_signals",
            "execute_orders",
            "analyze_portfolio"
        ]
    )
    
    # Create and start agent
    agent = create_agent_interface(config, audit_logger)
    await agent.start()
    
    # Generate trading signal
    signal = await agent.generate_trading_signal(
        symbol="AAPL",
        analysis_data={
            "current_price": 182.50,
            "indicators": {"rsi": 65.2, "macd": 1.8}
        }
    )
    
    print(f"AI Signal: {signal.signal_type.value} {signal.symbol}")
    print(f"Confidence: {signal.confidence:.2%}")
    
    # Execute order
    from moogztrade_agent_tools import OrderRequest
    order = OrderRequest(
        symbol="AAPL",
        order_type="market",
        side="buy",
        quantity=100
    )
    
    result = await agent.execute_order(order)
    print(f"Order Result: {result['status']}")
    
    # Analyze portfolio
    portfolio_data = {
        "portfolio_id": "portfolio_123",
        "total_value": 1000000,
        "positions": [
            {"symbol": "AAPL", "value": 500000},
            {"symbol": "GOOGL", "value": 300000}
        ]
    }
    
    risk_assessment = await agent.analyze_portfolio(portfolio_data)
    print(f"Risk Level: {risk_assessment.overall_risk.value}")
    print(f"Portfolio Beta: {risk_assessment.beta}")
    
    # Stop agent
    await agent.stop()

asyncio.run(agent_demo())
```

## Advanced Usage

### Custom Schema Validation

```python
from moogztrade_agent_tools import validate_trading_signal, validate_order_request
from pydantic import ValidationError

# Validate custom data
signal_data = {
    "symbol": "AAPL",
    "signal_type": "buy",
    "confidence": 0.95,
    "target_price": 185.50,
    "time_horizon": "1M",
    "reasoning": "Strong momentum indicators"
}

try:
    signal = validate_trading_signal(signal_data)
    print(f"Valid signal: {signal.symbol}")
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Market Analysis Schema

```python
from moogztrade_agent_tools import MarketAnalysis

# Create comprehensive market analysis
analysis = MarketAnalysis(
    analysis_type="technical",
    symbol="AAPL",
    timeframe="1D",
    overall_sentiment="bullish",
    key_metrics={
        "rsi": 65.2,
        "macd": 1.8,
        "volume_ratio": 1.5,
        "moving_average_50": 180.25,
        "moving_average_200": 175.80
    },
    support_levels=[175.00, 170.50, 165.00],
    resistance_levels=[185.00, 190.50, 195.00],
    trend_analysis={
        "short_term": "bullish",
        "medium_term": "bullish",
        "long_term": "neutral"
    },
    confidence_score=0.82
)

print(f"Analysis: {analysis.overall_sentiment} for {analysis.symbol}")
print(f"Confidence: {analysis.confidence_score:.2%}")
```

### Performance Metrics

```python
from moogztrade_agent_tools import PerformanceMetrics
from datetime import datetime, timedelta

# Create performance metrics
metrics = PerformanceMetrics(
    period_start=datetime.now() - timedelta(days=365),
    period_end=datetime.now(),
    total_return=0.156,  # 15.6%
    annualized_return=0.156,
    volatility=0.18,  # 18%
    sharpe_ratio=1.85,
    sortino_ratio=2.65,
    max_drawdown=-0.1234,  # -12.34%
    win_rate=0.65,  # 65%
    profit_factor=1.8,
    average_win=1250.00,
    average_loss=-680.00,
    total_trades=156,
    winning_trades=101
)

print(f"Annual Return: {metrics.annualized_return:.2%}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Win Rate: {metrics.win_rate:.2%}")
```

### Backtest Results

```python
from moogztrade_agent_tools import BacktestResult, PerformanceMetrics

# Create backtest result
backtest = BacktestResult(
    backtest_id="backtest_001",
    strategy_name="Momentum Strategy",
    start_date=datetime.now() - timedelta(days=365),
    end_date=datetime.now(),
    initial_capital=100000,
    final_capital=115600,
    total_return=0.156,
    performance_metrics=metrics,  # From previous example
    trades=[
        {"symbol": "AAPL", "entry": 175.50, "exit": 185.25, "pnl": 975.00},
        {"symbol": "GOOGL", "entry": 2800.00, "exit": 2950.00, "pnl": 1500.00}
    ],
    daily_returns=[0.001, 0.002, -0.001, 0.003, ...],  # Daily returns array
    benchmark_return=0.08  # 8% benchmark return
)

print(f"Strategy: {backtest.strategy_name}")
print(f"Total Return: {backtest.total_return:.2%}")
print(f"vs Benchmark: {backtest.total_return - backtest.benchmark_return:.2%}")
```

### Comprehensive Audit Trail

```python
import asyncio
from moogztrade_agent_tools import AuditLogger, AuditEventType, SeverityLevel

async def comprehensive_audit():
    logger = AuditLogger(log_file="comprehensive_audit.log")
    
    # Log agent lifecycle
    await logger.log_agent_start(
        agent_id="ai_trader_001",
        config={"strategy": "momentum", "risk_limit": 0.02}
    )
    
    # Log trading decisions
    await logger.log_signal_generated(
        agent_id="ai_trader_001",
        symbol="AAPL",
        signal_type="BUY",
        confidence=0.85,
        reasoning="RSI oversold with volume confirmation"
    )
    
    # Log API access
    await logger.log_api_access(
        endpoint="/api/v1/market-data",
        method="GET",
        user_id="user_123",
        ip_address="192.168.1.100",
        response_status=200,
        response_time=0.045
    )
    
    # Log security events
    await logger.log_security_event(
        event_type=AuditEventType.SECURITY_BREACH,
        description="Multiple failed login attempts detected",
        details={"attempts": 5, "ip": "192.168.1.200"},
        ip_address="192.168.1.200"
    )
    
    # Generate audit report
    from datetime import datetime, timedelta
    report = await logger.generate_audit_report(
        start_time=datetime.now() - timedelta(days=7),
        end_time=datetime.now()
    )
    
    print(f"Audit Report: {report['total_events']} events")
    print(f"Critical Events: {len(report['critical_events'])}")

asyncio.run(comprehensive_audit())
```

## Compliance and Governance

### Regulatory Compliance
The audit logging system supports major regulatory requirements:
- **SEC Rule 17a-5** - Record keeping for broker-dealers
- **MiFID II** - Markets in Financial Instruments Directive
- **FINRA Rules** - Financial Industry Regulatory Authority
- **GDPR** - Data protection and privacy

### Audit Trail Features
- Immutable logging with cryptographic hashes
- Complete transaction lifecycle tracking
- User action attribution
- System event correlation
- Automated compliance reporting

### Data Retention
Configurable retention policies support different regulatory requirements:
- Trade data: 7 years (SEC requirement)
- Order records: 6 years (FINRA requirement)
- Audit logs: 5-10 years (varies by jurisdiction)
- Personal data: Per GDPR requirements

## Performance and Scalability

### High-Volume Logging
The audit logger is optimized for high-volume trading environments:

```python
# Configure for high-frequency trading
logger = AuditLogger(
    log_file="hft_audit.log",
    buffer_size=5000,  # Larger buffer for HFT
    retention_days=2555  # 7 years for compliance
)
```

### Async Operations
All operations are fully async for maximum performance:

```python
# Concurrent audit logging
tasks = [
    logger.log_signal_generated(...),
    logger.log_order_event(...),
    logger.log_api_access(...)
]
await asyncio.gather(*tasks)
```

## License

Commercial Single-User License. See LICENSE.txt for details.

## Support

For enterprise support and custom implementations, contact:
- Email: enterprise@moogztrade.com
- Documentation: https://docs.moogztrade.com/agent-tools
- Support Portal: https://support.moogztrade.com

## Version History

- **v1.0.0** - Initial release with core schemas and audit logging
- Future versions will include:
  - Advanced ML model schemas
  - Multi-agent coordination
  - Real-time compliance monitoring
  - Automated reporting tools
