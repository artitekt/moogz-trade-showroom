# MoogzTrade Market Module

Real-time market data and async interface for trading applications.

## Overview

The Market Module provides high-performance access to real-time market data, portfolio management, and asynchronous trading interfaces. Built for speed and reliability in high-frequency trading environments.

## Features

### 📊 Real-Time Market Data
- Multi-exchange support (NYSE, NASDAQ, LSE, TSE, FX)
- WebSocket streaming for real-time updates
- Historical data access
- Market depth and order book data
- Smart caching with configurable TTL

### 💼 Portfolio Management
- Advanced portfolio optimization
- Mean-variance optimization
- Risk assessment and analytics
- Automated rebalancing
- Performance tracking

### ⚡ Async Interface
- High-performance async operations
- Concurrent data fetching
- Batch order execution
- WebSocket streaming
- Connection pooling and rate limiting

## Installation

```bash
pip install moogztrade-market
```

## Quick Start

### Market Data Provider

```python
import asyncio
from moogztrade_market import MarketDataProvider, Exchange

async def get_market_data():
    async with MarketDataProvider() as provider:
        # Get real-time data
        data = await provider.get_real_time_data("AAPL", Exchange.NYSE)
        print(f"AAPL Price: ${data.price}")
        print(f"Change: {data.change:+.2f} ({data.change_percent:+.2f}%)")
        
        # Get historical data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        historical = await provider.get_historical_data(
            "AAPL", Exchange.NYSE, start_date, end_date
        )
        print(f"Found {len(historical)} days of historical data")

# Run the async function
asyncio.run(get_market_data())
```

### Portfolio Management

```python
import asyncio
from moogztrade_market import PortfolioManager, RiskLevel

async def portfolio_demo():
    manager = PortfolioManager()
    
    # Create portfolio
    portfolio = await manager.create_portfolio(
        name="Growth Portfolio",
        initial_cash=100000,
        risk_level=RiskLevel.MODERATE
    )
    
    # Add positions
    await manager.add_position(
        portfolio.id, "AAPL", 100, 150.0, "Technology"
    )
    await manager.add_position(
        portfolio.id, "GOOGL", 50, 2800.0, "Technology"
    )
    
    # Get portfolio summary
    summary = await manager.get_portfolio_summary(portfolio.id)
    print(f"Portfolio Value: ${summary['summary']['total_value']:,.2f}")
    print(f"Total Return: {summary['summary']['total_return_percent']:+.2f}%")
    
    # Get rebalancing recommendations
    recommendations = await manager.rebalance_portfolio(portfolio.id)
    print(f"Rebalancing recommendations: {len(recommendations)}")

asyncio.run(portfolio_demo())
```

### Async Market Interface

```python
import asyncio
from moogztrade_market import AsyncMarketInterface

async def streaming_demo():
    async with AsyncMarketInterface() as interface:
        # Subscribe to real-time stream
        await interface.subscribe_to_stream(["AAPL", "GOOGL", "MSFT"])
        
        # Stream market data
        async for message in interface.stream_market_data(["AAPL"]):
            print(f"Stream update: {message.data}")
            # Break after 10 updates for demo
            if message.sequence > 10:
                break
        
        # Batch market data
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        batch_data = await interface.get_batch_market_data(symbols)
        
        for symbol, data in batch_data.items():
            print(f"{symbol}: ${data.price}")

asyncio.run(streaming_demo())
```

## Advanced Usage

### Custom Market Data Provider

```python
from moogztrade_market import MarketDataProvider, Exchange
import asyncio

async def custom_provider():
    # Custom cache TTL and API key
    provider = MarketDataProvider(
        api_key="your-api-key",
        cache_ttl_seconds=30  # 30 second cache
    )
    
    async with provider:
        # Get market summary
        summary = await provider.get_market_summary(Exchange.NYSE)
        print(f"Market Status: {summary['status']}")
        
        # Search symbols
        results = await provider.search_symbols("Apple")
        for result in results:
            print(f"Found: {result['symbol']} - {result['name']}")

asyncio.run(custom_provider())
```

### Portfolio Optimization

```python
import asyncio
import numpy as np
from moogztrade_market import PortfolioManager

async def portfolio_optimization():
    manager = PortfolioManager()
    
    # Create portfolio
    portfolio = await manager.create_portfolio(
        name="Optimized Portfolio",
        initial_cash=50000,
        risk_level=RiskLevel.AGGRESSIVE
    )
    
    # Mock returns data for optimization
    returns_data = {
        "AAPL": np.random.normal(0.001, 0.02, 252),  # Daily returns
        "GOOGL": np.random.normal(0.0008, 0.018, 252),
        "MSFT": np.random.normal(0.0009, 0.016, 252)
    }
    
    # Optimize portfolio
    optimization = await manager.optimize_portfolio(
        portfolio.id, returns_data
    )
    
    print(f"Expected Return: {optimization['expected_return']:.2%}")
    print(f"Volatility: {optimization['volatility']:.2%}")
    print(f"Sharpe Ratio: {optimization['sharpe_ratio']:.2f}")

asyncio.run(portfolio_optimization())
```

### High-Frequency Data Streaming

```python
import asyncio
from moogztrade_market import AsyncMarketInterface

async def high_frequency_streaming():
    # Configure for high-frequency trading
    interface = AsyncMarketInterface(
        ws_url="wss://stream.marketdata.com",
        max_connections=20  # More connections for HFT
    )
    
    async with interface:
        # Subscribe to multiple symbols
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA"]
        await interface.subscribe_to_stream(symbols)
        
        # Process stream with custom handler
        async for message in interface.stream_market_data(symbols):
            if message.type == "quote":
                # Process quote update
                quote_data = message.data
                # Your trading logic here
                pass
            elif message.type == "trade":
                # Process trade update
                trade_data = message.data
                # Your trading logic here
                pass

# For production use, you'd want proper error handling
# and connection management
```

## Performance Considerations

### Connection Pooling
The async interface uses connection pooling to optimize performance:

```python
# Configure for your use case
interface = AsyncMarketInterface(
    max_connections=10  # Adjust based on your needs
)
```

### Caching Strategy
Configure cache TTL based on your data freshness requirements:

```python
# Real-time trading (short cache)
provider = MarketDataProvider(cache_ttl_seconds=5)

# Analysis applications (longer cache)
provider = MarketDataProvider(cache_ttl_seconds=300)
```

### Batch Operations
Use batch operations for better performance:

```python
# Instead of multiple individual calls
symbols = ["AAPL", "GOOGL", "MSFT"]
batch_data = await interface.get_batch_market_data(symbols)

# Instead of individual orders
orders = [
    {"symbol": "AAPL", "side": "buy", "quantity": 100},
    {"symbol": "GOOGL", "side": "sell", "quantity": 50}
]
results = await interface.execute_batch_orders(orders)
```

## Data Sources

### Supported Exchanges
- **NYSE** - New York Stock Exchange
- **NASDAQ** - NASDAQ Stock Market
- **LSE** - London Stock Exchange
- **TSE** - Tokyo Stock Exchange
- **FX** - Foreign Exchange Markets

### Data Types
- **Real-time Quotes** - Bid/ask prices and sizes
- **Trades** - Executed trade information
- **Market Depth** - Order book data
- **Historical Data** - OHLCV data with custom intervals
- **Market Summaries** - Index data and market statistics

## Error Handling

The modules include comprehensive error handling:

```python
from moogztrade_market import MarketDataProvider
import asyncio

async def error_handling_demo():
    try:
        async with MarketDataProvider() as provider:
            data = await provider.get_real_time_data("INVALID", Exchange.NYSE)
    except ValueError as e:
        print(f"Invalid symbol: {e}")
    except ConnectionError as e:
        print(f"Connection failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(error_handling_demo())
```

## Monitoring and Analytics

Built-in metrics and monitoring:

```python
# Get provider statistics
provider = MarketDataProvider()
stats = await provider.get_statistics()
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"API calls made: {stats['api_calls']}")
print(f"Active subscriptions: {stats['active_subscriptions']}")
```

## License

Commercial Single-User License. See LICENSE.txt for details.

## Support

For enterprise support and custom implementations, contact:
- Email: enterprise@moogztrade.com
- Documentation: https://docs.moogztrade.com/market
- Support Portal: https://support.moogztrade.com

## Version History

- **v1.0.0** - Initial release with core market data features
- Future versions will include:
  - Additional exchange support
  - Options and derivatives data
  - Machine learning predictions
  - Advanced order types
