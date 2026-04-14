from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RESOLVED = "resolved"

class AlertManager:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.subscribers: List[callable] = []
    
    def create_alert(self, level: AlertLevel, message: str, source: str = "system") -> Dict[str, Any]:
        """Create a new alert"""
        alert = {
            "id": len(self.alerts) + 1,
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "source": source,
            "resolved": False
        }
        self.alerts.append(alert)
        self._notify_subscribers(alert)
        return alert
    
    def resolve_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Mark an alert as resolved"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.now().isoformat()
                self._notify_subscribers(alert)
                return alert
        return None
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all unresolved alerts"""
        return [a for a in self.alerts if not a.get("resolved", False)]
    
    def get_all_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all alerts with limit"""
        return self.alerts[-limit:]
    
    def subscribe(self, callback: callable):
        """Subscribe to alert notifications"""
        self.subscribers.append(callback)
    
    def _notify_subscribers(self, alert: Dict[str, Any]):
        """Notify all subscribers of new alert"""
        for subscriber in self.subscribers:
            try:
                subscriber(alert)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(self.get_active_alerts()),
            "critical": len([a for a in self.alerts if a["level"] == "critical"]),
            "warning": len([a for a in self.alerts if a["level"] == "warning"]),
            "info": len([a for a in self.alerts if a["level"] == "info"])
        }
