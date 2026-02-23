# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Market Data
# Licensing: Contact [Your Email]

"""
MoogzTrade Market Module
Real-time market data and async interface for trading applications
"""

from .data_provider import MarketDataProvider, create_market_data_provider, Exchange
from .portfolio_manager import PortfolioManager, create_portfolio_manager
from .async_interface import AsyncMarketInterface

__version__ = "1.0.0"
__author__ = "MoogzTrade Team"

__all__ = [
    "MarketDataProvider",
    "create_market_data_provider",
    "Exchange",
    "PortfolioManager", 
    "create_portfolio_manager",
    "AsyncMarketInterface"
]
