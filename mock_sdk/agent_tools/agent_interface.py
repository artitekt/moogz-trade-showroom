# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Agent Interface
# Licensing: Contact [Your Email]

"""
Agent Interface Module
High-level interface for AI trading agents
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Callable, AsyncIterator
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from .schemas import (
    TradingSignal, OrderRequest, PortfolioAllocation,
    RiskAssessment, MarketAnalysis, AgentConfig, AgentExecution
)
from .audit_logger import AuditLogger, AuditEventType, SeverityLevel


class AgentState(str, Enum):
    """Agent states"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"


class TaskPriority(str, Enum):
    """Task priorities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentTask:
    """Agent task data model"""
    task_id: str
    task_type: str
    priority: TaskPriority
    data: Dict[str, Any]
    created_at: datetime
    scheduled_at: datetime
    timeout_at: Optional[datetime]
    correlation_id: str


class AgentInterface:
    """High-level interface for AI trading agents"""
    
    def __init__(self, agent_config: AgentConfig, audit_logger: AuditLogger):
        """
        Initialize agent interface
        
        Args:
            agent_config: Agent configuration
            audit_logger: Audit logger instance
        """
        self.config = agent_config
        self.audit_logger = audit_logger
        self.state = AgentState.IDLE
        self.task_queue = asyncio.Queue()
        self.running = False
        self.execution_history: List[AgentExecution] = []
        self.current_task: Optional[AgentTask] = None
        self.logger = logging.getLogger(f"agent_{agent_config.agent_id}")
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
    
    async def start(self):
        """Start the agent"""
        if self.running:
            return
        
        self.running = True
        self.state = AgentState.IDLE
        
        # Log agent start
        await self.audit_logger.log_agent_start(
            agent_id=self.config.agent_id,
            config=self.config.dict()
        )
        
        # Start main execution loop
        asyncio.create_task(self._execution_loop())
        
        self.logger.info(f"Agent {self.config.agent_id} started")
    
    async def stop(self, reason: str = None):
        """Stop the agent"""
        if not self.running:
            return
        
        self.running = False
        self.state = AgentState.STOPPED
        
        # Log agent stop
        await self.audit_logger.log_agent_stop(
            agent_id=self.config.agent_id,
            reason=reason
        )
        
        self.logger.info(f"Agent {self.config.agent_id} stopped: {reason}")
    
    async def submit_task(self, task_type: str, data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         scheduled_at: datetime = None,
                         timeout_seconds: int = 300) -> str:
        """
        Submit a task to the agent
        
        Args:
            task_type: Type of task to execute
            data: Task data
            priority: Task priority
            scheduled_at: When to execute the task
            timeout_seconds: Task timeout in seconds
            
        Returns:
            Task ID
        """
        task_id = f"task_{datetime.now().timestamp()}_{hash(str(data)) % 10000}"
        correlation_id = f"corr_{datetime.now().timestamp()}"
        
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            data=data,
            created_at=datetime.now(),
            scheduled_at=scheduled_at or datetime.now(),
            timeout_at=datetime.now() + timedelta(seconds=timeout_seconds),
            correlation_id=correlation_id
        )
        
        # Add to queue
        await self.task_queue.put(task)
        
        self.logger.info(f"Task submitted: {task_type} (ID: {task_id})")
        
        return task_id
    
    async def generate_trading_signal(self, symbol: str, analysis_data: Dict[str, Any]) -> TradingSignal:
        """
        Generate a trading signal
        
        Args:
            symbol: Stock symbol
            analysis_data: Market analysis data
            
        Returns:
            Trading signal
        """
        task_id = await self.submit_task(
            task_type="generate_signal",
            data={"symbol": symbol, "analysis_data": analysis_data},
            priority=TaskPriority.HIGH
        )
        
        # Wait for completion (simplified for demo)
        await asyncio.sleep(1.0)
        
        # Mock signal generation
        from .schemas import SignalType, TradingSignal
        
        signal = TradingSignal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            confidence=0.85,
            target_price=analysis_data.get("current_price", 100) * 1.1,
            stop_loss=analysis_data.get("current_price", 100) * 0.95,
            time_horizon="1M",
            reasoning="Technical indicators show bullish momentum with strong volume support",
            indicators=analysis_data.get("indicators", {}),
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        # Log signal generation
        await self.audit_logger.log_signal_generated(
            agent_id=self.config.agent_id,
            symbol=symbol,
            signal_type=signal.signal_type.value,
            confidence=signal.confidence,
            reasoning=signal.reasoning
        )
        
        return signal
    
    async def execute_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """
        Execute a trading order
        
        Args:
            order_request: Order request details
            
        Returns:
            Order execution result
        """
        task_id = await self.submit_task(
            task_type="execute_order",
            data={"order": order_request.dict()},
            priority=TaskPriority.CRITICAL
        )
        
        # Wait for completion (simplified for demo)
        await asyncio.sleep(0.5)
        
        # Mock order execution
        result = {
            "order_id": f"order_{datetime.now().timestamp()}",
            "status": "filled",
            "filled_quantity": order_request.quantity,
            "average_price": order_request.price or 100.0,
            "execution_time": datetime.now().isoformat(),
            "commission": 1.0
        }
        
        # Log order event
        await self.audit_logger.log_order_event(
            event_type=AuditEventType.ORDER_FILLED,
            order_id=result["order_id"],
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=result["filled_quantity"],
            price=result["average_price"],
            agent_id=self.config.agent_id
        )
        
        return result
    
    async def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> RiskAssessment:
        """
        Analyze portfolio risk
        
        Args:
            portfolio_data: Portfolio data
            
        Returns:
            Risk assessment
        """
        task_id = await self.submit_task(
            task_type="analyze_portfolio",
            data={"portfolio": portfolio_data},
            priority=TaskPriority.MEDIUM
        )
        
        # Wait for completion (simplified for demo)
        await asyncio.sleep(2.0)
        
        # Mock risk assessment
        from .schemas import RiskLevel, RiskAssessment
        
        assessment = RiskAssessment(
            portfolio_id=portfolio_data.get("portfolio_id", "unknown"),
            overall_risk=RiskLevel.MEDIUM,
            var_95=portfolio_data.get("total_value", 100000) * 0.02,
            var_99=portfolio_data.get("total_value", 100000) * 0.03,
            beta=1.15,
            sharpe_ratio=1.8,
            max_drawdown=-0.12,
            volatility=0.18,
            concentration_risk={"Technology": 0.45, "Healthcare": 0.25, "Finance": 0.30},
            liquidity_risk=0.3
        )
        
        # Log risk assessment
        await self.audit_logger.log_risk_assessment(
            portfolio_id=assessment.portfolio_id,
            risk_score=0.65,  # Normalized risk score
            risk_factors={
                "beta": assessment.beta,
                "volatility": assessment.volatility,
                "concentration": max(assessment.concentration_risk.values())
            },
            agent_id=self.config.agent_id
        )
        
        return assessment
    
    async def rebalance_portfolio(self, current_allocation: PortfolioAllocation,
                                target_allocation: Dict[str, float]) -> List[OrderRequest]:
        """
        Generate portfolio rebalancing orders
        
        Args:
            current_allocation: Current portfolio allocation
            target_allocation: Target allocation
            
        Returns:
            List of rebalancing orders
        """
        task_id = await self.submit_task(
            task_type="rebalance_portfolio",
            data={
                "current": current_allocation.dict(),
                "target": target_allocation
            },
            priority=TaskPriority.HIGH
        )
        
        # Wait for completion (simplified for demo)
        await asyncio.sleep(1.5)
        
        # Mock rebalancing orders
        orders = []
        total_value = current_allocation.total_value
        
        for asset_class, target_weight in target_allocation.items():
            current_weight = current_allocation.allocations.get(asset_class, 0)
            
            if abs(current_weight - target_weight) > 0.05:  # 5% threshold
                diff = target_weight - current_weight
                amount = diff * total_value
                
                if diff > 0:  # Buy
                    orders.append(OrderRequest(
                        symbol=f"{asset_class.upper}_ETF",
                        order_type="market",
                        side="buy",
                        quantity=amount / 100,  # Mock price
                        price=100.0
                    ))
                else:  # Sell
                    orders.append(OrderRequest(
                        symbol=f"{asset_class.upper}_ETF",
                        order_type="market",
                        side="sell",
                        quantity=abs(amount) / 100,
                        price=100.0
                    ))
        
        # Log portfolio rebalancing
        await self.audit_logger.log_event(
            event_type=AuditEventType.PORTFOLIO_REBALANCED,
            source=self.config.agent_id,
            description=f"Portfolio rebalanced with {len(orders)} orders",
            details={"orders_count": len(orders), "total_amount": total_value},
            severity=SeverityLevel.MEDIUM,
            tags=["portfolio", "rebalancing"]
        )
        
        return orders
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.config.agent_id,
            "state": self.state.value,
            "running": self.running,
            "current_task": self.current_task.task_id if self.current_task else None,
            "queue_size": self.task_queue.qsize(),
            "metrics": self.metrics,
            "config": self.config.dict(),
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_execution_history(self, limit: int = 100) -> List[AgentExecution]:
        """Get agent execution history"""
        return self.execution_history[-limit:]
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    async def _execution_loop(self):
        """Main agent execution loop"""
        while self.running:
            try:
                # Get next task
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # Check if task is scheduled for future
                if task.scheduled_at > datetime.now():
                    # Re-queue for later
                    await asyncio.sleep(1.0)
                    await self.task_queue.put(task)
                    continue
                
                # Check if task has timed out
                if task.timeout_at and task.timeout_at < datetime.now():
                    self.logger.warning(f"Task {task.task_id} timed out")
                    continue
                
                # Execute task
                await self._execute_task(task)
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
                self.state = AgentState.ERROR
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: AgentTask):
        """Execute a single task"""
        self.current_task = task
        self.state = AgentState.THINKING
        
        start_time = datetime.now()
        
        try:
            self.state = AgentState.EXECUTING
            
            # Execute task based on type
            result = await self._process_task(task)
            
            # Record execution
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = AgentExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                agent_id=self.config.agent_id,
                task_type=task.task_type,
                input_data=task.data,
                output_data=result,
                execution_time=execution_time,
                success=True,
                created_at=datetime.now()
            )
            
            self.execution_history.append(execution)
            
            # Update metrics
            self.metrics["tasks_completed"] += 1
            self.metrics["total_execution_time"] += execution_time
            self.metrics["average_execution_time"] = (
                self.metrics["total_execution_time"] / self.metrics["tasks_completed"]
            )
            
            self.logger.info(f"Task {task.task_id} completed in {execution_time:.2f}s")
            
        except Exception as e:
            # Record failed execution
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = AgentExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                agent_id=self.config.agent_id,
                task_type=task.task_type,
                input_data=task.data,
                output_data={},
                execution_time=execution_time,
                success=False,
                error_message=str(e),
                created_at=datetime.now()
            )
            
            self.execution_history.append(execution)
            
            # Update metrics
            self.metrics["tasks_failed"] += 1
            
            self.logger.error(f"Task {task.task_id} failed: {e}")
            
            # Log error
            await self.audit_logger.log_event(
                event_type=AuditEventType.ERROR_OCCURRED,
                source=self.config.agent_id,
                description=f"Task execution failed: {task.task_type}",
                details={"error": str(e), "task_id": task.task_id},
                severity=SeverityLevel.HIGH,
                correlation_id=task.correlation_id
            )
            
        finally:
            self.current_task = None
            self.state = AgentState.IDLE
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process a task based on its type"""
        # This would contain the actual AI/ML logic
        # For demo, we'll return mock results
        
        if task.task_type == "generate_signal":
            return {"signal": "BUY", "confidence": 0.85}
        elif task.task_type == "execute_order":
            return {"status": "filled", "order_id": "mock_order_123"}
        elif task.task_type == "analyze_portfolio":
            return {"risk_score": 0.65, "recommendation": "HOLD"}
        elif task.task_type == "rebalance_portfolio":
            return {"orders_generated": 3, "total_amount": 50000}
        else:
            return {"status": "completed", "result": "mock_result"}


def create_agent_interface(agent_config: AgentConfig, audit_logger: AuditLogger) -> AgentInterface:
    """Create a new agent interface"""
    return AgentInterface(agent_config, audit_logger)
