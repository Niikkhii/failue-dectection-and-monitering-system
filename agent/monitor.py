import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

class MonitoringAgent:
    def __init__(self, db, alert_manager, detection_engine):
        self.db = db
        self.alert_manager = alert_manager
        self.detection_engine = detection_engine
        self.is_running = False
        self.metrics_history: Dict[str, List[float]] = {}
    
    async def start(self):
        """Start the monitoring agent"""
        self.is_running = True
        print("Monitoring agent started")
        await self.collect_metrics()
    
    async def stop(self):
        """Stop the monitoring agent"""
        self.is_running = False
        print("Monitoring agent stopped")
    
    async def collect_metrics(self):
        """Continuously collect system metrics"""
        while self.is_running:
            try:
                # Simulate metric collection
                metrics = {
                    "cpu": random.uniform(20, 75),
                    "memory": random.uniform(30, 80),
                    "disk": random.uniform(40, 70),
                    "error_rate": random.uniform(0.1, 3.0)
                }
                
                # Store metrics
                for name, value in metrics.items():
                    self.db.insert_metric(name, value)
                    
                    # Track history for anomaly detection
                    if name not in self.metrics_history:
                        self.metrics_history[name] = []
                    self.metrics_history[name].append(value)
                    
                    # Check for anomalies
                    if self.detection_engine.detect_anomaly(self.metrics_history[name]):
                        self.alert_manager.create_alert(
                            level="warning",
                            message=f"Anomaly detected in {name}: {value:.2f}",
                            source="monitor_agent"
                        )
                    
                    # Check thresholds
                    alert = self.detection_engine.check_metric(name, value)
                    if alert:
                        self.alert_manager.create_alert(
                            level="critical" if alert["level"] == "critical" else "warning",
                            message=f"{name.upper()} threshold exceeded: {value:.2f} > {alert['threshold']}",
                            source="threshold_check"
                        )
                
                # Store event
                self.db.insert_event("metrics_collected", str(metrics))
                
                # Wait before next collection
                await asyncio.sleep(5)
            
            except Exception as e:
                print(f"Error in metric collection: {e}")
                await asyncio.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "is_running": self.is_running,
            "metrics_tracked": len(self.metrics_history),
            "active_alerts": len(self.alert_manager.get_active_alerts())
        }
