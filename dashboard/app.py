from typing import Dict, Any

class DashboardService:
    def __init__(self, db, alert_manager, detection_engine):
        self.db = db
        self.alert_manager = alert_manager
        self.detection_engine = detection_engine
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get operator-friendly dashboard data"""
        processed_metrics = self.db.get_latest_processed_metrics(limit=20)
        active_alerts = self.alert_manager.get_active_alerts()
        return {
            "processed_metrics": processed_metrics,
            "alerts": active_alerts,
            "stats": self.alert_manager.get_stats(),
            "status": self.get_health_status(),
            "events": self.db.get_events(limit=20),
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary from processed batch data"""
        processed_metrics = self.db.get_latest_processed_metrics(limit=100)

        summary = {}
        for metric in processed_metrics:
            metric_type = metric.get("metric_type", "unknown")
            if metric_type not in summary:
                summary[metric_type] = {
                    "batches": 0,
                    "anomalies": 0,
                    "means": [],
                    "mins": [],
                    "maxs": [],
                }

            summary[metric_type]["batches"] += 1
            summary[metric_type]["means"].append(metric.get("mean", 0))
            summary[metric_type]["mins"].append(metric.get("min_value", 0))
            summary[metric_type]["maxs"].append(metric.get("max_value", 0))
            if metric.get("anomaly_detected"):
                summary[metric_type]["anomalies"] += 1

        for metric_type, data in summary.items():
            means = data.pop("means")
            mins = data.pop("mins")
            maxs = data.pop("maxs")
            data["overall_mean"] = sum(means) / len(means) if means else 0
            data["overall_min"] = min(mins) if mins else 0
            data["overall_max"] = max(maxs) if maxs else 0

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
