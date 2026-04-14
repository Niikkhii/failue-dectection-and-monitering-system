from alerting.alerts import AlertManager
from storage.database import Database


def test_database_raw_and_processed_metrics(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.insert_raw_metric("cpu", 45.5)
    db.insert_raw_metric("memory", 60.0)
    assert db.get_raw_metrics_count() == 2

    grouped = db.get_last_n_raw_metrics(10)
    assert "cpu" in grouped
    assert "memory" in grouped

    db.insert_processed_metric(
        metric_type="cpu",
        mean=45.5,
        min_val=40.0,
        max_val=50.0,
        std_dev=3.0,
        anomaly=False,
        threshold_exceeded=False,
    )
    processed = db.get_latest_processed_metrics(limit=5)
    assert len(processed) == 1
    assert processed[0]["metric_type"] == "cpu"


def test_alert_persistence_and_reload(tmp_path):
    db = Database(str(tmp_path / "alerts.db"))
    manager = AlertManager(db=db)
    created = manager.create_alert("warning", "CPU high", source="test")
    assert created["id"] > 0

    manager2 = AlertManager(db=db)
    manager2.load_active_from_db()
    all_alerts = manager2.get_all_alerts(limit=10)
    assert len(all_alerts) == 1
    assert all_alerts[0]["message"] == "CPU high"
