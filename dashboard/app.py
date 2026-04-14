from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

class DashboardService:
    def __init__(self, db, alert_manager, detection_engine):
        self.db = db
        self.alert_manager = alert_manager
        self.detection_engine = detection_engine
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all dashboard data"""
        return {
            "metrics": self.db.get_metrics(limit=20),
            "alerts": self.alert_manager.get_all_alerts(limit=20),
            "stats": self.alert_manager.get_stats(),
            "events": self.db.get_events(limit=20)
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        metrics = self.db.get_metrics(limit=100)
        
        summary = {}
        for metric in metrics:
            name = metric.get("name", "unknown")
            if name not in summary:
                summary[name] = {"count": 0, "values": []}
            summary[name]["count"] += 1
            summary[name]["values"].append(metric.get("value", 0))
        
        # Calculate statistics
        for name in summary:
            values = summary[name]["values"]
            summary[name]["avg"] = sum(values) / len(values) if values else 0
            summary[name]["min"] = min(values) if values else 0
            summary[name]["max"] = max(values) if values else 0
        
        return summary
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = len([a for a in active_alerts if a["level"] == "critical"])
        warning_alerts = len([a for a in active_alerts if a["level"] == "warning"])
        
        if critical_alerts > 0:
            status = "critical"
        elif warning_alerts > 0:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "active_alerts": len(active_alerts)
        }
