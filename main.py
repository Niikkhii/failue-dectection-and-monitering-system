import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from storage.database import Database
from alerting.alerts import AlertManager, AlertLevel
from detector.engine import DetectionEngine
from agent.monitor import MonitoringAgent
from dashboard.app import DashboardService

# Initialize components
db = Database("monitoring.db")
alert_manager = AlertManager()
detection_engine = DetectionEngine()
monitoring_agent = MonitoringAgent(db, alert_manager, detection_engine)
dashboard_service = DashboardService(db, alert_manager, detection_engine)

# Create FastAPI app
app = FastAPI(title="Monitoring System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MetricData(BaseModel):
    name: str
    value: float
    tags: Optional[str] = None

class AlertData(BaseModel):
    level: str
    message: str
    source: Optional[str] = "api"

# Startup event
@app.on_event("startup")
async def startup():
    """Start background tasks on app startup"""
    asyncio.create_task(monitoring_agent.start())
    print("Monitoring system started")

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Clean up on app shutdown"""
    await monitoring_agent.stop()
    print("Monitoring system stopped")

# Health endpoints
@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "monitoring-system"}

# Metrics endpoints
@app.get("/metrics")
def get_metrics(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent metrics"""
    return db.get_metrics(limit=limit)

@app.post("/metrics")
def add_metric(metric: MetricData) -> Dict[str, Any]:
    """Add a new metric"""
    metric_id = db.insert_metric(metric.name, metric.value, metric.tags)
    return {"id": metric_id, "status": "created"}

# Alerts endpoints
@app.get("/alerts")
def get_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent alerts"""
    return alert_manager.get_all_alerts(limit=limit)

@app.get("/alerts/active")
def get_active_alerts() -> List[Dict[str, Any]]:
    """Get active alerts"""
    return alert_manager.get_active_alerts()

@app.post("/alerts")
def create_alert(alert: AlertData) -> Dict[str, Any]:
    """Create a new alert"""
    level = AlertLevel[alert.level.upper()]
    return alert_manager.create_alert(level, alert.message, alert.source)

@app.put("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int) -> Dict[str, Any]:
    """Resolve an alert"""
    resolved = alert_manager.resolve_alert(alert_id)
    if resolved:
        return {"status": "resolved", "alert": resolved}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.get("/alerts/stats")
def get_alert_stats() -> Dict[str, Any]:
    """Get alert statistics"""
    return alert_manager.get_stats()

# Events endpoints
@app.get("/events")
def get_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent events"""
    return db.get_events(limit=limit)

# Dashboard endpoints
@app.get("/dashboard")
def get_dashboard() -> Dict[str, Any]:
    """Get dashboard data"""
    return dashboard_service.get_dashboard_data()

@app.get("/dashboard/metrics-summary")
def get_metrics_summary() -> Dict[str, Any]:
    """Get metrics summary"""
    return dashboard_service.get_metrics_summary()

@app.get("/dashboard/health")
def get_health_status() -> Dict[str, Any]:
    """Get system health status"""
    return dashboard_service.get_health_status()

# Agent endpoints
@app.get("/agent/status")
def get_agent_status() -> Dict[str, Any]:
    """Get monitoring agent status"""
    return monitoring_agent.get_status()

# Root endpoint
@app.get("/")
def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "Monitoring System",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "alerts": "/alerts",
            "dashboard": "/dashboard",
            "agent": "/agent/status"
        }
    }
