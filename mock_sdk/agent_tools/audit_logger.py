"""
Mock Audit Logger
Simulated audit logging for demo purposes
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class AuditLogger:
    """Mock audit logger for demo purposes"""
    
    def __init__(self):
        """Initialize mock audit logger"""
        self.audit_logs = []
        self.log_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
    
    def log_action(self, user_id: str, action: str, details: Dict[str, Any], level: str = "INFO") -> str:
        """Mock action logging"""
        log_entry = {
            "log_id": f"log_{len(self.audit_logs) + 1:06d}",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details,
            "level": level,
            "ip_address": "192.168.1.100",  # Mock IP
            "user_agent": "Mozilla/5.0 (Demo Browser)",  # Mock user agent
            "session_id": f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        self.audit_logs.append(log_entry)
        return log_entry["log_id"]
    
    def get_logs(self, user_id: Optional[str] = None, action: Optional[str] = None, 
                 level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get filtered audit logs"""
        filtered_logs = self.audit_logs
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log["user_id"] == user_id]
        
        if action:
            filtered_logs = [log for log in filtered_logs if log["action"] == action]
        
        if level:
            filtered_logs = [log for log in filtered_logs if log["level"] == level]
        
        return filtered_logs[-limit:]
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get mock security events"""
        security_actions = ["LOGIN", "LOGOUT", "API_KEY_GENERATED", "API_KEY_REVOKED", "PERMISSION_DENIED"]
        security_logs = []
        
        for log in self.audit_logs:
            if log["action"] in security_actions:
                log_time = datetime.fromisoformat(log["timestamp"])
                hours_ago = datetime.now().timestamp() - (hours * 3600)
                if log_time.timestamp() > hours_ago:
                    security_logs.append(log)
        
        return security_logs
    
    def generate_compliance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate mock compliance report"""
        return {
            "report_id": f"compliance_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "period": {"start": start_date, "end": end_date},
            "total_actions": len(self.audit_logs),
            "unique_users": len(set(log["user_id"] for log in self.audit_logs)),
            "security_events": len(self.get_security_events(24 * 30)),  # Last 30 days
            "failed_attempts": len([log for log in self.audit_logs if log["level"] in ["ERROR", "CRITICAL"]]),
            "api_key_operations": len([log for log in self.audit_logs if "API_KEY" in log["action"]]),
            "generated_at": datetime.now().isoformat(),
            "compliance_status": "COMPLIANT"
        }
    
    def export_logs(self, format: str = "json") -> str:
        """Export audit logs in specified format"""
        if format.lower() == "json":
            return json.dumps(self.audit_logs, indent=2, default=str)
        elif format.lower() == "csv":
            # Simple CSV format for demo
            csv_lines = ["timestamp,user_id,action,level,details"]
            for log in self.audit_logs:
                csv_lines.append(f"{log['timestamp']},{log['user_id']},{log['action']},{log['level']},\"{json.dumps(log['details'])}\"")
            return "\n".join(csv_lines)
        else:
            return "Unsupported format"
