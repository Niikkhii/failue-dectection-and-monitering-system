from detector.engine import DetectionEngine


def test_threshold_check_and_update():
    engine = DetectionEngine()

    assert engine.check_metric("cpu", 50.0) is None

    alert = engine.check_metric("cpu", 81.0)
    assert alert is not None
    assert alert["metric"] == "cpu"
    assert alert["level"] == "warning"

    engine.update_threshold("cpu", 90.0)
    assert engine.check_metric("cpu", 85.0) is None


def test_anomaly_detection_window():
    engine = DetectionEngine()
    stable = [50.0] * 10
    assert engine.detect_anomaly(stable) is False
