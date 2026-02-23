# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Portfolio Manager
# Licensing: Contact [Your Email]

"""
Portfolio Manager Module
Advanced portfolio optimization and rebalancing
"""

import asyncio
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import sys
import os
import uuid
import threading
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from moogz_trade_sdk.agent_tools.audit_logger import AuditLogger, AuditEventType, SeverityLevel
except ImportError:
    # Fallback for standalone testing
    class AuditLogger:
        def log_event(self, *args, **kwargs):
            pass
    class AuditEventType:
        PORTFOLIO_REBALANCED = "portfolio_rebalanced"
    class SeverityLevel:
        LOW = "low"
        MEDIUM = "medium"


class RebalanceFrequency(Enum):
    """Portfolio rebalancing frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class RiskLevel(Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class TransactionState(Enum):
    """Two-Phase Commit transaction states"""
    PREPARING = "preparing"
    PREPARED = "prepared"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ABORTING = "aborting"
    ABORTED = "aborted"


class TransactionPhase(Enum):
    """Two-Phase Commit phases"""
    PREPARE = "prepare"
    COMMIT = "commit"
    ABORT = "abort"


@dataclass
class TransactionParticipant:
    """Transaction participant for 2PC"""
    name: str
    prepare_func: Callable
    commit_func: Callable
    abort_func: Callable
    state: TransactionState = TransactionState.PREPARING


@dataclass
class Transaction:
    """Two-Phase Commit transaction"""
    transaction_id: str
    participants: List[TransactionParticipant]
    created_at: datetime
    timeout: timedelta = timedelta(seconds=30)
    state: TransactionState = TransactionState.PREPARING


@dataclass
class Position:
    """Portfolio position"""
    symbol: str
    shares: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    weight: float
    sector: Optional[str] = None
    last_updated: datetime = None


@dataclass
class Portfolio:
    """Portfolio data model"""
    id: str
    name: str
    total_value: float
    cash_balance: float
    positions: List[Position]
    created_at: datetime
    last_updated: datetime
    risk_level: RiskLevel
    target_allocation: Dict[str, float]
    performance_metrics: Dict[str, float]


@dataclass
class RebalanceRecommendation:
    """Portfolio rebalancing recommendation"""
    symbol: str
    current_weight: float
    target_weight: float
    action: str  # "buy" or "sell"
    shares: float
    amount: float
    reason: str


class PortfolioManager:
    """Enterprise portfolio manager with Two-Phase Commit support"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize portfolio manager
        
        Args:
            risk_free_rate: Risk-free rate for calculations
        """
        self.risk_free_rate = risk_free_rate
        self.portfolios: Dict[str, Portfolio] = {}
        self.logger = logging.getLogger(__name__)
        self.audit_logger = AuditLogger()
        
        # Two-Phase Commit infrastructure
        self.active_transactions: Dict[str, Transaction] = {}
        self.transaction_lock = threading.RLock()
        self._transaction_cleanup_task: Optional[asyncio.Task] = None
    
    async def create_portfolio(self, name: str, initial_cash: float,
                             risk_level: RiskLevel = RiskLevel.MODERATE,
                             target_allocation: Dict[str, float] = None) -> Portfolio:
        """
        Create a new portfolio
        
        Args:
            name: Portfolio name
            initial_cash: Initial cash balance
            risk_level: Risk tolerance level
            target_allocation: Target asset allocation
            
        Returns:
            Created portfolio
        """
        portfolio_id = f"portfolio_{datetime.now().timestamp()}"
        
        # Set default target allocation based on risk level
        if not target_allocation:
            target_allocation = self._get_default_allocation(risk_level)
        
        portfolio = Portfolio(
            id=portfolio_id,
            name=name,
            total_value=initial_cash,
            cash_balance=initial_cash,
            positions=[],
            created_at=datetime.now(),
            last_updated=datetime.now(),
            risk_level=risk_level,
            target_allocation=target_allocation,
            performance_metrics={}
        )
        
        self.portfolios[portfolio_id] = portfolio
        self.logger.info(f"Created portfolio {portfolio_id} with ${initial_cash:,.2f}")
        
        # Log to audit
        self.audit_logger.log_event(
            event_type=AuditEventType.PORTFOLIO_REBALANCED,
            source="portfolio_manager",
            description=f"Portfolio {portfolio_id} created with ${initial_cash:,.2f} initial cash",
            details={
                "portfolio_id": portfolio_id,
                "portfolio_name": name,
                "initial_cash": initial_cash,
                "risk_level": risk_level.value
            },
            severity=SeverityLevel.LOW,
            tags=["portfolio", "creation"]
        )
        
        return portfolio
    
    async def add_position(self, portfolio_id: str, symbol: str, shares: float,
                          price: float, sector: str = None) -> Position:
        """
        Add or update a position in a portfolio
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            shares: Number of shares
            price: Purchase price
            sector: Stock sector
            
        Returns:
            Updated position
        """
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        cost = shares * price
        
        # Check if sufficient cash
        if portfolio.cash_balance < cost:
            raise ValueError(f"Insufficient cash: need ${cost:,.2f}, have ${portfolio.cash_balance:,.2f}")
        
        # Deduct cash from portfolio
        portfolio.cash_balance -= cost
        
        # Check if position already exists
        existing_position = None
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                existing_position = pos
                break
        
        if existing_position:
            # Update existing position
            total_shares = existing_position.shares + shares
            total_cost = (existing_position.shares * existing_position.average_cost) + (shares * price)
            new_average_cost = total_cost / total_shares
            
            existing_position.shares = total_shares
            existing_position.average_cost = new_average_cost
            existing_position.current_price = price
            existing_position.market_value = total_shares * price
            existing_position.unrealized_pnl = (price - new_average_cost) * total_shares
            existing_position.unrealized_pnl_percent = ((price - new_average_cost) / new_average_cost) * 100
            existing_position.last_updated = datetime.now()
            
            position = existing_position
        else:
            # Create new position
            position = Position(
                symbol=symbol,
                shares=shares,
                average_cost=price,
                current_price=price,
                market_value=shares * price,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                weight=0.0,
                sector=sector,
                last_updated=datetime.now()
            )
            portfolio.positions.append(position)
        
        # Update portfolio
        await self._update_portfolio_metrics(portfolio_id)
        
        # Log to audit
        self.audit_logger.log_event(
            event_type=AuditEventType.PORTFOLIO_REBALANCED,
            source="portfolio_manager",
            description=f"Position {symbol} {'added/updated' if existing_position else 'created'} in portfolio {portfolio_id}",
            details={
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "shares": shares,
                "price": price,
                "action": "update" if existing_position else "create",
                "total_shares": position.shares,
                "market_value": position.market_value
            },
            severity=SeverityLevel.MEDIUM,
            tags=["portfolio", "position"]
        )
        
        return position
    
    async def remove_position(self, portfolio_id: str, symbol: str, shares: float = None) -> bool:
        """
        Remove or reduce a position in a portfolio
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            shares: Number of shares to remove (None to remove all)
            
        Returns:
            True if successful
        """
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        for i, position in enumerate(portfolio.positions):
            if position.symbol == symbol:
                if shares is None or shares >= position.shares:
                    # Remove entire position
                    portfolio.cash_balance += position.market_value
                    portfolio.positions.pop(i)
                else:
                    # Reduce position
                    sale_value = shares * position.current_price
                    portfolio.cash_balance += sale_value
                    
                    position.shares -= shares
                    position.market_value = position.shares * position.current_price
                    position.unrealized_pnl = (position.current_price - position.average_cost) * position.shares
                    position.unrealized_pnl_percent = ((position.current_price - position.average_cost) / position.average_cost) * 100
                    position.last_updated = datetime.now()
                
                await self._update_portfolio_metrics(portfolio_id)
                
                # Log to audit
                self.audit_logger.log_event(
                    event_type=AuditEventType.PORTFOLIO_REBALANCED,
                    source="portfolio_manager",
                    description=f"Position {symbol} {'removed entirely' if shares is None or shares >= position.shares else 'reduced'} in portfolio {portfolio_id}",
                    details={
                        "portfolio_id": portfolio_id,
                        "symbol": symbol,
                        "shares_removed": shares if shares is not None else position.shares,
                        "sale_value": sale_value if shares is not None and shares < position.shares else position.market_value,
                        "action": "remove" if shares is None or shares >= position.shares else "reduce"
                    },
                    severity=SeverityLevel.MEDIUM,
                    tags=["portfolio", "position"]
                )
                
                return True
        
        return False
    
    async def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """
        Get portfolio summary with performance metrics
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio summary
        """
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Calculate performance metrics
        total_invested = sum(pos.shares * pos.average_cost for pos in portfolio.positions)
        total_value = sum(pos.market_value for pos in portfolio.positions) + portfolio.cash_balance
        total_pnl = total_value - (total_invested + portfolio.cash_balance)
        total_return = (total_pnl / (total_invested + portfolio.cash_balance)) * 100 if total_invested > 0 else 0
        
        # Sector allocation
        sector_allocation = {}
        for pos in portfolio.positions:
            sector = pos.sector or "Unknown"
            if sector not in sector_allocation:
                sector_allocation[sector] = 0
            sector_allocation[sector] += pos.weight
        
        return {
            "portfolio": asdict(portfolio),
            "summary": {
                "total_value": total_value,
                "total_invested": total_invested,
                "cash_balance": portfolio.cash_balance,
                "total_pnl": total_pnl,
                "total_return_percent": total_return,
                "position_count": len(portfolio.positions),
                "sector_allocation": sector_allocation
            },
            "performance": portfolio.performance_metrics
        }
    
    async def rebalance_portfolio(self, portfolio_id: str) -> List[RebalanceRecommendation]:
        """
        Generate rebalancing recommendations
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of rebalancing recommendations
        """
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Pre-group positions by sector for O(n) performance
        sector_positions = {}
        for pos in portfolio.positions:
            sector = pos.sector or "Unknown"
            if sector not in sector_positions:
                sector_positions[sector] = []
            sector_positions[sector].append(pos)
        
        recommendations = []
        total_value = portfolio.total_value
        
        for target_sector, target_weight in portfolio.target_allocation.items():
            sector_positions_list = sector_positions.get(target_sector, [])
            current_weight = sum(pos.weight for pos in sector_positions_list)
            
            if abs(current_weight - target_weight) > 0.05:  # 5% threshold
                diff = target_weight - current_weight
                target_amount = diff * total_value
                
                if sector_positions_list:
                    # Distribute across positions in sector
                    sector_total_value = sum(p.market_value for p in sector_positions_list)
                    for pos in sector_positions_list:
                        pos_weight = pos.market_value / sector_total_value if sector_total_value > 0 else 0
                        action = "buy" if diff > 0 else "sell"
                        amount = target_amount * pos_weight
                        shares = amount / pos.current_price if action == "buy" else amount / pos.current_price
                        
                        recommendations.append(RebalanceRecommendation(
                            symbol=pos.symbol,
                            current_weight=current_weight,
                            target_weight=target_weight,
                            action=action,
                            shares=abs(shares),
                            amount=abs(amount),
                            reason=f"Rebalance {target_sector} allocation from {current_weight:.1%} to {target_weight:.1%}"
                        ))
        
        return recommendations
    
    async def optimize_portfolio(self, portfolio_id: str, returns_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Optimize portfolio using mean-variance optimization
        
        Args:
            portfolio_id: Portfolio ID
            returns_data: Historical returns data for assets
            
        Returns:
            Optimization results
        """
        # Mock implementation - in real scenario would use modern portfolio theory
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Simple equal weight optimization for demo
        symbols = list(returns_data.keys())
        optimal_weights = [1.0 / len(symbols)] * len(symbols)
        
        return {
            "symbols": symbols,
            "optimal_weights": optimal_weights,
            "expected_return": 0.08,  # 8% expected return
            "volatility": 0.15,       # 15% volatility
            "sharpe_ratio": 0.4,      # Sharpe ratio
            "risk_level": portfolio.risk_level.value
        }
    
    async def _update_portfolio_metrics(self, portfolio_id: str):
        """Update portfolio metrics and weights"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return
        
        # Recalculate market values based on current prices
        for position in portfolio.positions:
            position.market_value = position.shares * position.current_price
            position.unrealized_pnl = (position.current_price - position.average_cost) * position.shares
            if position.average_cost > 0:
                position.unrealized_pnl_percent = ((position.current_price - position.average_cost) / position.average_cost) * 100
        
        # Update position weights
        total_equity_value = sum(pos.market_value for pos in portfolio.positions)
        
        for position in portfolio.positions:
            if total_equity_value > 0:
                position.weight = position.market_value / total_equity_value
            else:
                position.weight = 0.0
        
        # Update portfolio total value
        portfolio.total_value = total_equity_value + portfolio.cash_balance
        portfolio.last_updated = datetime.now()
        
        # Calculate performance metrics
        portfolio.performance_metrics = await self._calculate_performance_metrics(portfolio)
    
    async def _calculate_performance_metrics(self, portfolio: Portfolio) -> Dict[str, float]:
        """Calculate portfolio performance metrics"""
        if not portfolio.positions:
            return {}
        
        # Mock calculations for demo
        total_pnl = sum(pos.unrealized_pnl for pos in portfolio.positions)
        total_invested = sum(pos.shares * pos.average_cost for pos in portfolio.positions)
        
        return {
            "daily_return": 0.0124,      # 1.24% daily return
            "weekly_return": 0.0345,     # 3.45% weekly return
            "monthly_return": 0.0892,    # 8.92% monthly return
            "yearly_return": 0.156,      # 15.6% yearly return
            "sharpe_ratio": 1.85,
            "max_drawdown": -0.1234,     # -12.34% max drawdown
            "volatility": 0.18,          # 18% volatility
            "beta": 1.12,
            "alpha": 0.023
        }
    
    def _get_default_allocation(self, risk_level: RiskLevel) -> Dict[str, float]:
        """Get default asset allocation based on risk level"""
        allocations = {
            RiskLevel.CONSERVATIVE: {
                "Bonds": 0.60,
                "Large Cap Stocks": 0.25,
                "International Stocks": 0.10,
                "Cash": 0.05
            },
            RiskLevel.MODERATE: {
                "Large Cap Stocks": 0.40,
                "International Stocks": 0.20,
                "Bonds": 0.25,
                "Real Estate": 0.10,
                "Cash": 0.05
            },
            RiskLevel.AGGRESSIVE: {
                "Large Cap Stocks": 0.35,
                "Small Cap Stocks": 0.25,
                "International Stocks": 0.20,
                "Emerging Markets": 0.10,
                "Real Estate": 0.05,
                "Cash": 0.05
            }
        }
        
        return allocations.get(risk_level, allocations[RiskLevel.MODERATE])
    
    def create_transaction(self, timeout_seconds: int = 30) -> str:
        """
        Create a new Two-Phase Commit transaction
        
        Args:
            timeout_seconds: Transaction timeout in seconds
            
        Returns:
            Transaction ID
        """
        transaction_id = f"txn_{uuid.uuid4().hex}"
        transaction = Transaction(
            transaction_id=transaction_id,
            participants=[],
            created_at=datetime.now(),
            timeout=timedelta(seconds=timeout_seconds)
        )
        
        with self.transaction_lock:
            self.active_transactions[transaction_id] = transaction
        
        self.logger.info(f"Created 2PC transaction {transaction_id}")
        return transaction_id
    
    def add_participant(self, transaction_id: str, name: str,
                       prepare_func: Callable, commit_func: Callable, abort_func: Callable):
        """
        Add a participant to a transaction
        
        Args:
            transaction_id: Transaction ID
            name: Participant name
            prepare_func: Prepare phase function
            commit_func: Commit phase function
            abort_func: Abort phase function
        """
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.state != TransactionState.PREPARING:
                raise ValueError(f"Cannot add participants to transaction in {transaction.state.value} state")
            
            participant = TransactionParticipant(
                name=name,
                prepare_func=prepare_func,
                commit_func=commit_func,
                abort_func=abort_func
            )
            
            transaction.participants.append(participant)
            self.logger.info(f"Added participant {name} to transaction {transaction_id}")
    
    async def prepare_transaction(self, transaction_id: str) -> bool:
        """
        Execute prepare phase of Two-Phase Commit
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if all participants prepared successfully
        """
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.state != TransactionState.PREPARING:
                raise ValueError(f"Transaction {transaction_id} not in PREPARING state")
            
            transaction.state = TransactionState.PREPARED
        
        try:
            # Execute prepare phase for all participants
            for participant in transaction.participants:
                try:
                    await participant.prepare_func()
                    participant.state = TransactionState.PREPARED
                    self.logger.info(f"Participant {participant.name} prepared successfully")
                except Exception as e:
                    self.logger.error(f"Participant {participant.name} failed to prepare: {e}")
                    # Abort on first failure
                    await self.abort_transaction(transaction_id)
                    return False
            
            self.logger.info(f"All participants prepared for transaction {transaction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Prepare phase failed for transaction {transaction_id}: {e}")
            await self.abort_transaction(transaction_id)
            return False
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """
        Execute commit phase of Two-Phase Commit
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if all participants committed successfully
        """
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            if transaction.state != TransactionState.PREPARED:
                raise ValueError(f"Transaction {transaction_id} not in PREPARED state")
            
            transaction.state = TransactionState.COMMITTING
        
        try:
            # Execute commit phase for all participants
            commit_results = []
            for participant in transaction.participants:
                try:
                    await participant.commit_func()
                    participant.state = TransactionState.COMMITTED
                    commit_results.append(True)
                    self.logger.info(f"Participant {participant.name} committed successfully")
                except Exception as e:
                    self.logger.error(f"Participant {participant.name} failed to commit: {e}")
                    commit_results.append(False)
            
            success = all(commit_results)
            
            with self.transaction_lock:
                transaction.state = TransactionState.COMMITTED if success else TransactionState.ABORTED
            
            if success:
                self.logger.info(f"All participants committed for transaction {transaction_id}")
                # Clean up committed transaction
                await self._cleanup_transaction(transaction_id)
            else:
                self.logger.error(f"Commit phase failed for transaction {transaction_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Commit phase failed for transaction {transaction_id}: {e}")
            with self.transaction_lock:
                transaction.state = TransactionState.ABORTED
            return False
    
    async def abort_transaction(self, transaction_id: str) -> bool:
        """
        Abort a transaction
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if transaction aborted successfully
        """
        with self.transaction_lock:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            transaction.state = TransactionState.ABORTING
        
        try:
            # Execute abort phase for all prepared participants
            for participant in transaction.participants:
                if participant.state == TransactionState.PREPARED:
                    try:
                        await participant.abort_func()
                        participant.state = TransactionState.ABORTED
                        self.logger.info(f"Participant {participant.name} aborted successfully")
                    except Exception as e:
                        self.logger.error(f"Participant {participant.name} failed to abort: {e}")
            
            with self.transaction_lock:
                transaction.state = TransactionState.ABORTED
            
            self.logger.info(f"Transaction {transaction_id} aborted")
            # Clean up aborted transaction
            await self._cleanup_transaction(transaction_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Abort phase failed for transaction {transaction_id}: {e}")
            return False
    
    async def execute_transaction(self, transaction_id: str) -> bool:
        """
        Execute complete Two-Phase Commit transaction
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if transaction committed successfully
        """
        try:
            # Prepare phase
            if not await self.prepare_transaction(transaction_id):
                return False
            
            # Commit phase
            return await self.commit_transaction(transaction_id)
            
        except Exception as e:
            self.logger.error(f"Transaction {transaction_id} failed: {e}")
            await self.abort_transaction(transaction_id)
            return False
    
    @contextmanager
    def transaction_context(self, timeout_seconds: int = 30):
        """
        Context manager for automatic transaction management
        
        Args:
            timeout_seconds: Transaction timeout in seconds
            
        Yields:
            Transaction ID
        """
        transaction_id = self.create_transaction(timeout_seconds)
        try:
            yield transaction_id
            # Note: Actual commit/abort must be handled by caller
        except Exception as e:
            # Auto-abort on exception
            asyncio.create_task(self.abort_transaction(transaction_id))
            raise e
    
    async def _cleanup_transaction(self, transaction_id: str):
        """Clean up completed transaction"""
        with self.transaction_lock:
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
                self.logger.info(f"Cleaned up transaction {transaction_id}")
    
    async def cleanup_expired_transactions(self):
        """Clean up expired transactions"""
        now = datetime.now()
        expired_transactions = []
        
        with self.transaction_lock:
            for txn_id, transaction in self.active_transactions.items():
                if now - transaction.created_at > transaction.timeout:
                    expired_transactions.append(txn_id)
        
        for txn_id in expired_transactions:
            self.logger.warning(f"Transaction {txn_id} expired, aborting...")
            await self.abort_transaction(txn_id)
    
    async def add_position_2pc(self, portfolio_id: str, symbol: str, shares: float,
                              price: float, sector: str = None) -> Position:
        """
        Add position using Two-Phase Commit for atomic operation
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            shares: Number of shares
            price: Purchase price
            sector: Stock sector
            
        Returns:
            Updated position
        """
        async def prepare_position_update():
            """Prepare phase: validate and reserve resources"""
            portfolio = self.portfolios.get(portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            cost = shares * price
            if portfolio.cash_balance < cost:
                raise ValueError(f"Insufficient cash: need ${cost:,.2f}, have ${portfolio.cash_balance:,.2f}")
            
            # Reserve cash (simulate by temporary deduction)
            portfolio.cash_balance -= cost
            return True
        
        async def commit_position_update():
            """Commit phase: finalize position update"""
            portfolio = self.portfolios.get(portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # Find existing position
            existing_position = None
            for pos in portfolio.positions:
                if pos.symbol == symbol:
                    existing_position = pos
                    break
            
            if existing_position:
                # Update existing position
                total_shares = existing_position.shares + shares
                total_cost = (existing_position.shares * existing_position.average_cost) + (shares * price)
                new_average_cost = total_cost / total_shares
                
                existing_position.shares = total_shares
                existing_position.average_cost = new_average_cost
                existing_position.current_price = price
                existing_position.market_value = total_shares * price
                existing_position.unrealized_pnl = (price - new_average_cost) * total_shares
                existing_position.unrealized_pnl_percent = ((price - new_average_cost) / new_average_cost) * 100
                existing_position.last_updated = datetime.now()
                position = existing_position
            else:
                # Create new position
                position = Position(
                    symbol=symbol,
                    shares=shares,
                    average_cost=price,
                    current_price=price,
                    market_value=shares * price,
                    unrealized_pnl=0.0,
                    unrealized_pnl_percent=0.0,
                    weight=0.0,
                    sector=sector,
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            # Update portfolio metrics
            await self._update_portfolio_metrics(portfolio_id)
            return position
        
        async def abort_position_update():
            """Abort phase: rollback cash reservation"""
            portfolio = self.portfolios.get(portfolio_id)
            if portfolio:
                cost = shares * price
                portfolio.cash_balance += cost  # Return reserved cash
        
        async def prepare_audit_log():
            """Prepare phase: validate audit logging"""
            return True  # Audit logging always available
        
        async def commit_audit_log():
            """Commit phase: log successful operation"""
            self.audit_logger.log_event(
                event_type=AuditEventType.PORTFOLIO_REBALANCED,
                source="portfolio_manager_2pc",
                description=f"Position {symbol} added via 2PC in portfolio {portfolio_id}",
                details={
                    "portfolio_id": portfolio_id,
                    "symbol": symbol,
                    "shares": shares,
                    "price": price,
                    "action": "create_2pc",
                    "transaction_id": "pending"
                },
                severity=SeverityLevel.MEDIUM,
                tags=["portfolio", "position", "2pc"]
            )
        
        async def abort_audit_log():
            """Abort phase: log aborted operation"""
            self.audit_logger.log_event(
                event_type=AuditEventType.PORTFOLIO_REBALANCED,
                source="portfolio_manager_2pc",
                description=f"Position {symbol} operation aborted in portfolio {portfolio_id}",
                details={
                    "portfolio_id": portfolio_id,
                    "symbol": symbol,
                    "shares": shares,
                    "price": price,
                    "action": "abort_2pc",
                    "reason": "transaction_failed"
                },
                severity=SeverityLevel.MEDIUM,
                tags=["portfolio", "position", "2pc", "abort"]
            )
        
        # Create and execute transaction
        transaction_id = self.create_transaction()
        
        # Add participants
        self.add_participant(transaction_id, "position_update", 
                            prepare_position_update, commit_position_update, abort_position_update)
        self.add_participant(transaction_id, "audit_log",
                            prepare_audit_log, commit_audit_log, abort_audit_log)
        
        # Execute transaction
        success = await self.execute_transaction(transaction_id)
        
        if not success:
            raise RuntimeError(f"2PC transaction {transaction_id} failed")
        
        # Return the updated position
        portfolio = self.portfolios.get(portfolio_id)
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                return pos
        
        raise RuntimeError(f"Position {symbol} not found after successful transaction")


def create_portfolio_manager(risk_free_rate: float = 0.02) -> PortfolioManager:
    """Create a new portfolio manager"""
    return PortfolioManager(risk_free_rate)
