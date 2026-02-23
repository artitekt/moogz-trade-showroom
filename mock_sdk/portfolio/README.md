# MoogzTrade Portfolio Module

Core infrastructure components for trading applications.

## Components

- **Network Utilities**: Circuit breaker pattern and request signing
- **Storage**: Memory and Redis storage backends

## Features

- Circuit breaker for resilience
- HMAC request signing for security
- In-memory storage for development
- Redis storage for production
- Async/await support
- Comprehensive error handling

## Installation

```bash
pip install moogztrade-portfolio
```

## Usage

```python
from moogztrade_portfolio import CircuitBreaker, MemoryStorage, RedisStorage

# Initialize circuit breaker
breaker = CircuitBreaker()

# Initialize storage
memory_storage = MemoryStorage()
redis_storage = RedisStorage()
```

## Licensing

(c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
This source code is proprietary and confidential.
Version: 1.1.0-GOLD | Module: Portfolio
Licensing: Contact [Your Email]
