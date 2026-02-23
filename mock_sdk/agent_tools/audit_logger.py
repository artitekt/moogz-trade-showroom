# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Audit Logger
# Licensing: Contact [Your Email]

"""
Audit Logger Module
Comprehensive audit logging for AI trading agents
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
import hashlib
import uuid


class AuditEventType(str, Enum):
    """Audit event types"""
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    ORDER_CREATED = "order_created"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    SIGNAL_GENERATED = "signal_generated"
    PORTFOLIO_REBALANCED = "portfolio_rebalanced"
    RISK_ASSESSMENT = "risk_assessment"
    API_ACCESS = "api_access"
    CONFIG_CHANGE = "config_change"
    ERROR_OCCURRED = "error_occurred"
    SECURITY_BREACH = "security_breach"
    DATA_ACCESS = "data_access"
    MODEL_EXECUTION = "model_execution"


class SeverityLevel(str, Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data model"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    severity: SeverityLevel
    source: str  # Agent ID, user ID, or system component
    description: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: List[str] = None
    previous_hash: Optional[str] = None  # SHA-256 hash of previous entry for chaining
    current_hash: Optional[str] = None   # SHA-256 hash of current entry
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AuditLogger:
    """Enterprise audit logger for AI trading systems"""
    
    def __init__(self, log_file: str = "audit.log", 
                 retention_days: int = 365,
                 buffer_size: int = 1000,
                 enable_compression: bool = True):
        """
        Initialize audit logger
        
        Args:
            log_file: Path to audit log file
            retention_days: Number of days to retain logs
            buffer_size: Buffer size for batch writes
            enable_compression: Enable log compression
        """
        self.log_file = Path(log_file)
        self.retention_days = retention_days
        self.buffer_size = buffer_size
        self.enable_compression = enable_compression
        self.buffer: List[AuditEvent] = []
        self.logger = logging.getLogger("audit_logger")
        self._last_hash: Optional[str] = None  # Track last hash for chaining
        
        # Create log directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup file logger
        self._setup_logger()
        
        # Initialize last hash from existing log file
        self._initialize_last_hash()
    
    def log_event(self, event_type: AuditEventType, source: str, description: str,
                  details: Dict[str, Any] = None, severity: SeverityLevel = SeverityLevel.MEDIUM,
                  user_id: str = None, session_id: str = None, ip_address: str = None,
                  user_agent: str = None, correlation_id: str = None, tags: List[str] = None) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of audit event
            source: Source of the event (agent, user, system)
            description: Human-readable description
            details: Additional event details
            severity: Event severity
            user_id: User ID if applicable
            session_id: Session ID if applicable
            ip_address: IP address if applicable
            user_agent: User agent if applicable
            correlation_id: Correlation ID for tracing
            tags: Event tags
            
        Returns:
            Event ID
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            severity=severity,
            source=source,
            description=description,
            details=details or {},
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            tags=tags or [],
            previous_hash=self._last_hash
        )
        
        # Calculate current hash for chaining
        event.current_hash = self._calculate_event_hash(event)
        
        # Update last hash for next entry
        self._last_hash = event.current_hash
        
        # Add to buffer
        self.buffer.append(event)
        
        # Write buffer if full
        if len(self.buffer) >= self.buffer_size:
            asyncio.create_task(self._flush_buffer())
        
        # Log critical events immediately
        if severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
            asyncio.create_task(self._flush_buffer())
        
        return event.event_id
    
    async def log_agent_start(self, agent_id: str, config: Dict[str, Any],
                            user_id: str = None, session_id: str = None) -> str:
        """Log agent start event"""
        return self.log_event(
            event_type=AuditEventType.AGENT_START,
            source=agent_id,
            description=f"Agent {agent_id} started",
            details={"config": config},
            severity=SeverityLevel.LOW,
            user_id=user_id,
            session_id=session_id,
            tags=["agent", "lifecycle"]
        )
    
    async def log_agent_stop(self, agent_id: str, reason: str = None,
                           user_id: str = None, session_id: str = None) -> str:
        """Log agent stop event"""
        details = {}
        if reason:
            details["reason"] = reason
        
        return self.log_event(
            event_type=AuditEventType.AGENT_STOP,
            source=agent_id,
            description=f"Agent {agent_id} stopped",
            details=details,
            severity=SeverityLevel.LOW,
            user_id=user_id,
            session_id=session_id,
            tags=["agent", "lifecycle"]
        )
    
    async def log_order_event(self, event_type: AuditEventType, order_id: str,
                            symbol: str, side: str, quantity: float, price: float,
                            agent_id: str = None, user_id: str = None) -> str:
        """Log order-related events"""
        details = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price
        }
        
        if agent_id:
            details["agent_id"] = agent_id
        
        return self.log_event(
            event_type=event_type,
            source=agent_id or user_id or "system",
            description=f"Order {event_type.value}: {side} {quantity} {symbol} @ ${price}",
            details=details,
            severity=SeverityLevel.MEDIUM,
            user_id=user_id,
            tags=["order", "trading"]
        )
    
    async def log_signal_generated(self, agent_id: str, symbol: str, signal_type: str,
                                 confidence: float, reasoning: str) -> str:
        """Log trading signal generation"""
        return self.log_event(
            event_type=AuditEventType.SIGNAL_GENERATED,
            source=agent_id,
            description=f"Trading signal generated: {signal_type} {symbol} (confidence: {confidence:.2f})",
            details={
                "symbol": symbol,
                "signal_type": signal_type,
                "confidence": confidence,
                "reasoning": reasoning
            },
            severity=SeverityLevel.MEDIUM,
            tags=["signal", "trading", "ai"]
        )
    
    async def log_risk_assessment(self, portfolio_id: str, risk_score: float,
                                risk_factors: Dict[str, Any], agent_id: str = None) -> str:
        """Log risk assessment"""
        return self.log_event(
            event_type=AuditEventType.RISK_ASSESSMENT,
            source=agent_id or "system",
            description=f"Risk assessment for portfolio {portfolio_id}: {risk_score:.2f}",
            details={
                "portfolio_id": portfolio_id,
                "risk_score": risk_score,
                "risk_factors": risk_factors
            },
            severity=SeverityLevel.MEDIUM,
            tags=["risk", "portfolio"]
        )
    
    async def log_api_access(self, endpoint: str, method: str, user_id: str,
                           ip_address: str, user_agent: str = None,
                           response_status: int = None, response_time: float = None) -> str:
        """Log API access events"""
        details = {
            "endpoint": endpoint,
            "method": method,
            "response_status": response_status,
            "response_time": response_time
        }
        
        # Determine severity based on response status
        severity = SeverityLevel.LOW
        if response_status and response_status >= 400:
            severity = SeverityLevel.MEDIUM if response_status < 500 else SeverityLevel.HIGH
        
        return self.log_event(
            event_type=AuditEventType.API_ACCESS,
            source=user_id,
            description=f"API access: {method} {endpoint}",
            details=details,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            tags=["api", "access"]
        )
    
    async def log_security_event(self, event_type: AuditEventType, description: str,
                               details: Dict[str, Any], ip_address: str = None,
                               user_id: str = None) -> str:
        """Log security-related events"""
        return self.log_event(
            event_type=event_type,
            source="security_system",
            description=description,
            details=details,
            severity=SeverityLevel.CRITICAL,
            user_id=user_id,
            ip_address=ip_address,
            tags=["security", "alert"]
        )
    
    async def search_events(self, query: Dict[str, Any] = None,
                           start_time: datetime = None, end_time: datetime = None,
                           event_types: List[AuditEventType] = None,
                           sources: List[str] = None,
                           severity_levels: List[SeverityLevel] = None,
                           limit: int = 1000) -> List[AuditEvent]:
        """
        Search audit events
        
        Args:
            query: Search query parameters
            start_time: Start time filter
            end_time: End time filter
            event_types: Event type filter
            sources: Source filter
            severity_levels: Severity level filter
            limit: Maximum number of results
            
        Returns:
            List of matching audit events
        """
        # In a real implementation, this would query a database
        # For demo, we'll search through the buffer and recent logs
        
        events = []
        
        # Search buffer first
        for event in self.buffer:
            if self._matches_query(event, query, start_time, end_time, 
                                 event_types, sources, severity_levels):
                events.append(event)
        
        # TODO: Search log file for older events
        
        return events[:limit]
    
    async def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Get a specific audit event by ID"""
        # Search buffer first
        for event in self.buffer:
            if event.event_id == event_id:
                return event
        
        # TODO: Search log file
        
        return None
    
    async def get_events_by_correlation(self, correlation_id: str) -> List[AuditEvent]:
        """Get all events with the same correlation ID"""
        events = []
        
        for event in self.buffer:
            if event.correlation_id == correlation_id:
                events.append(event)
        
        # TODO: Search log file
        
        return events
    
    async def generate_audit_report(self, start_time: datetime, end_time: datetime,
                                  event_types: List[AuditEventType] = None) -> Dict[str, Any]:
        """
        Generate audit report for a time period
        
        Args:
            start_time: Report start time
            end_time: Report end time
            event_types: Event types to include
            
        Returns:
            Audit report data
        """
        events = await self.search_events(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types,
            limit=10000
        )
        
        # Generate statistics
        report = {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_events": len(events),
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_source": {},
            "top_sources": [],
            "critical_events": [],
            "trends": {}
        }
        
        # Calculate statistics
        for event in events:
            # Count by type
            event_type = event.event_type.value
            report["events_by_type"][event_type] = report["events_by_type"].get(event_type, 0) + 1
            
            # Count by severity
            severity = event.severity.value
            report["events_by_severity"][severity] = report["events_by_severity"].get(severity, 0) + 1
            
            # Count by source
            source = event.source
            report["events_by_source"][source] = report["events_by_source"].get(source, 0) + 1
            
            # Collect critical events
            if event.severity == SeverityLevel.CRITICAL:
                report["critical_events"].append(asdict(event))
        
        # Sort top sources
        report["top_sources"] = sorted(
            report["events_by_source"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return report
    
    async def _flush_buffer(self):
        """Flush audit buffer to file"""
        if not self.buffer:
            return
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                for event in self.buffer:
                    log_entry = self._format_log_entry(event)
                    f.write(log_entry + '\n')
            
            self.buffer.clear()
            
        except Exception as e:
            self.logger.error(f"Failed to flush audit buffer: {e}")
    
    def _format_log_entry(self, event: AuditEvent) -> str:
        """Format audit event for logging"""
        log_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "severity": event.severity.value,
            "source": event.source,
            "description": event.description,
            "details": event.details,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "correlation_id": event.correlation_id,
            "tags": event.tags,
            "previous_hash": event.previous_hash,
            "current_hash": event.current_hash
        }
        
        return json.dumps(log_data, default=str)
    
    def _calculate_event_hash(self, event: AuditEvent) -> str:
        """
        Calculate SHA-256 hash for event chaining
        
        Args:
            event: Audit event to hash
            
        Returns:
            SHA-256 hash as hex string
        """
        # Create canonical representation for hashing
        hash_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "severity": event.severity.value,
            "source": event.source,
            "description": event.description,
            "details": event.details,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "correlation_id": event.correlation_id,
            "tags": sorted(event.tags),  # Sort for deterministic ordering
            "previous_hash": event.previous_hash
        }
        
        # Convert to JSON string with sorted keys for deterministic output
        canonical_json = json.dumps(hash_data, sort_keys=True, default=str)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    def _initialize_last_hash(self):
        """Initialize last hash from existing log file for continuity"""
        if not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get the last valid log entry
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    if 'current_hash' in log_entry:
                        self._last_hash = log_entry['current_hash']
                        self.logger.info(f"Initialized hash chain from existing log: {self._last_hash[:16]}...")
                        break
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Failed to initialize hash chain from log file: {e}")
    
    def verify_log_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the audit log using hash chaining
        
        Returns:
            Integrity verification results
        """
        if not self.log_file.exists():
            return {"valid": True, "message": "Log file does not exist"}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return {"valid": True, "message": "Empty log file"}
            
            previous_hash = None
            valid_entries = 0
            invalid_entries = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    log_entry = json.loads(line)
                    
                    # Verify hash chain
                    if 'current_hash' not in log_entry:
                        invalid_entries.append(f"Line {i+1}: Missing current_hash")
                        continue
                    
                    if 'previous_hash' not in log_entry:
                        invalid_entries.append(f"Line {i+1}: Missing previous_hash")
                        continue
                    
                    # Check if previous hash matches
                    if previous_hash and log_entry['previous_hash'] != previous_hash:
                        invalid_entries.append(f"Line {i+1}: Hash chain broken - expected {previous_hash[:16]}..., got {log_entry['previous_hash'][:16]}...")
                        continue
                    
                    # Verify current hash
                    event = AuditEvent(
                        event_id=log_entry['event_id'],
                        event_type=AuditEventType(log_entry['event_type']),
                        timestamp=datetime.fromisoformat(log_entry['timestamp']),
                        severity=SeverityLevel(log_entry['severity']),
                        source=log_entry['source'],
                        description=log_entry['description'],
                        details=log_entry['details'],
                        user_id=log_entry.get('user_id'),
                        session_id=log_entry.get('session_id'),
                        ip_address=log_entry.get('ip_address'),
                        user_agent=log_entry.get('user_agent'),
                        correlation_id=log_entry.get('correlation_id'),
                        tags=log_entry.get('tags', []),
                        previous_hash=log_entry.get('previous_hash')
                    )
                    
                    calculated_hash = self._calculate_event_hash(event)
                    if calculated_hash != log_entry['current_hash']:
                        invalid_entries.append(f"Line {i+1}: Hash mismatch - calculated {calculated_hash[:16]}..., expected {log_entry['current_hash'][:16]}...")
                        continue
                    
                    previous_hash = log_entry['current_hash']
                    valid_entries += 1
                    
                except json.JSONDecodeError:
                    invalid_entries.append(f"Line {i+1}: Invalid JSON")
                except Exception as e:
                    invalid_entries.append(f"Line {i+1}: {str(e)}")
            
            return {
                "valid": len(invalid_entries) == 0,
                "total_entries": len([l for l in lines if l.strip()]),
                "valid_entries": valid_entries,
                "invalid_entries": len(invalid_entries),
                "errors": invalid_entries[:10],  # Limit error output
                "last_hash": previous_hash
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to verify log integrity: {str(e)}"
            }
    
    def _matches_query(self, event: AuditEvent, query: Dict[str, Any],
                       start_time: datetime, end_time: datetime,
                       event_types: List[AuditEventType],
                       sources: List[str],
                       severity_levels: List[SeverityLevel]) -> bool:
        """Check if event matches search criteria"""
        # Time filter
        if start_time and event.timestamp < start_time:
            return False
        if end_time and event.timestamp > end_time:
            return False
        
        # Event type filter
        if event_types and event.event_type not in event_types:
            return False
        
        # Source filter
        if sources and event.source not in sources:
            return False
        
        # Severity filter
        if severity_levels and event.severity not in severity_levels:
            return False
        
        # Custom query filter
        if query:
            for key, value in query.items():
                if hasattr(event, key) and getattr(event, key) != value:
                    return False
                if key in event.details and event.details[key] != value:
                    return False
        
        return True
    
    def _setup_logger(self):
        """Setup file logger for audit events"""
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)


# Convenience functions
def create_audit_logger(log_file: str = "audit.log", 
                       retention_days: int = 365) -> AuditLogger:
    """Create a new audit logger"""
    return AuditLogger(log_file, retention_days)
