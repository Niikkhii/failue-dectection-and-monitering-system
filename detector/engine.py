from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class DetectionEngine:
    def __init__(self):
        self.thresholds = {
            "cpu": 80.0,
            "memory": 85.0,
            "disk": 90.0,
            "error_rate": 5.0
        }
        self.alert_history = []
    
    def check_metric(self, metric_name: str, value: float) -> Optional[Dict[str, Any]]:
        """Check if a metric exceeds thresholds"""
        if metric_name in self.thresholds:
            threshold = self.thresholds[metric_name]
            if value >= threshold:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "metric": metric_name,
                    "value": value,
                    "threshold": threshold,
                    "status": "alert",
                    "level": "critical" if value >= threshold * 1.2 else "warning"
                }
                self.alert_history.append(alert)
                return alert
        return None
    
    def detect_anomaly(self, metrics: List[float], window: int = 10) -> bool:
        """Detect anomalies in time series data"""
        if len(metrics) < window:
            return False
        
        recent = metrics[-window:]
        avg = sum(recent) / len(recent)
        std_dev = (sum((x - avg) ** 2 for x in recent) / len(recent)) ** 0.5
        
        # Anomaly if latest value is more than 2 std devs from mean
        if abs(recent[-1] - avg) > 2 * std_dev:
            return True
        return False
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self.alert_history
    
    def clear_history(self):
        """Clear alert history"""
        self.alert_history = []
    
    def update_threshold(self, metric: str, threshold: float):
        """Update threshold for a metric"""
        self.thresholds[metric] = threshold
