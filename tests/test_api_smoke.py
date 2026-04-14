from fastapi.testclient import TestClient

import main


def test_health_and_thresholds_endpoints():
    client = TestClient(main.app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    thresholds = client.get("/thresholds")
    assert thresholds.status_code == 200
    assert "cpu" in thresholds.json()

    update = client.put("/thresholds/cpu", json={"value": 70.0})
    assert update.status_code == 200
    assert update.json()["new_threshold"] == 70.0
