from locust import HttpUser, task, between, events

class MonitoringSystemUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        self.headers = {"Content-Type": "application/json"}
    
    @task(3)
    def get_metrics(self):
        """Get metrics - most common"""
        self.client.get("/metrics?limit=50")
    
    @task(2)
    def get_alerts(self):
        """Get alerts"""
        self.client.get("/alerts?limit=20")
    
    @task(1)
    def add_metric(self):
        """Add a metric"""
        payload = {
            "name": "test_metric",
            "value": 42.5,
            "tags": "test"
        }
        self.client.post("/metrics", json=payload)
    
    @task(2)
    def get_dashboard(self):
        """Get dashboard data"""
        self.client.get("/dashboard")
    
    @task(1)
    def get_health_status(self):
        """Get health status"""
        self.client.get("/dashboard/health")
    
    @task(1)
    def health_check(self):
        """Health check"""
        self.client.get("/health")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test started")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test stopped")
