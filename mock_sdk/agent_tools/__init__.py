# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Agent Tools
# Licensing: Contact [Your Email]

"""
MoogzTrade Agent Tools Module
Pydantic schemas and audit logging for AI trading agents
"""

from .schemas import (
    TradingSignal, OrderRequest, PortfolioAllocation,
    RiskAssessment, MarketAnalysis, AgentConfig
)
from .audit_logger import AuditLogger, AuditEvent, AuditEventType
from .agent_interface import AgentInterface, create_agent_interface

__version__ = "1.0.0"
__author__ = "MoogzTrade Team"

__all__ = [
    "TradingSignal",
    "OrderRequest", 
    "PortfolioAllocation",
    "RiskAssessment",
    "MarketAnalysis",
    "AgentConfig",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AgentInterface",
    "create_agent_interface"
]
