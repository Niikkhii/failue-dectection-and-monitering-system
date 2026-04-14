from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RESOLVED = "resolved"

class AlertManager:
    def __init__(self, db=None):
        self.db = db
        self.alerts: List[Dict[str, Any]] = []
        self.subscribers: List[callable] = []
    
    def load_active_from_db(self):
        """Load unresolved alerts from DB into memory on startup."""
        if not self.db:
            return
        self.alerts = self.db.get_alerts(limit=1000)

    def create_alert(
        self,
        level: AlertLevel | str,
        message: str,
        source: str = "system",
        metric_type: Optional[str] = None,
        value: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create a new alert"""
        level_value = level.value if isinstance(level, AlertLevel) else str(level).lower()
        alert_id = (
            self.db.insert_alert(level_value, message, source, metric_type, value, threshold)
            if self.db
            else len(self.alerts) + 1
        )
        alert = {
            "id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "level": level_value,
            "message": message,
            "source": source,
            "metric_type": metric_type,
            "value": value,
            "threshold": threshold,
            "resolved": False,
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
                if self.db:
                    self.db.resolve_alert(alert_id)
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
