# Detailed Change Tracker

This file tracks major architecture and implementation changes made to this project.

## 2026-04-14 - Real Metrics + Batch Processing Refactor

### 1) Core Architecture Change
- Switched from single-process random metric generation to two-process design:
  - Collector process (`metrics_collector.py`) writes raw metrics every 5 seconds.
  - Monitoring API process (`main.py` + `agent/monitor.py`) reads raw data and processes in batches.

### 2) Data Pipeline Change
- Previous flow:
  - `agent/monitor.py` generated random values and directly inserted them.
- New flow:
  - Real host metrics from `psutil` -> `raw_metrics` table -> batch processing -> `processed_metrics` table -> dashboard APIs.

### 3) Database Layer Changes (`storage/database.py`)
- Added `raw_metrics` table:
  - `metric_type`, `value`, `server`, `tags`, `timestamp`.
- Added `processed_metrics` table:
  - `mean`, `min_value`, `max_value`, `std_dev`, `anomaly_detected`, `threshold_exceeded`, `batch_timestamp`.
- Added methods:
  - `insert_raw_metric`
  - `get_raw_metrics_count`
  - `get_last_n_raw_metrics`
  - `clear_raw_metrics`
  - `insert_processed_metric`
  - `get_latest_processed_metrics`
- Kept compatibility:
  - `insert_metric` now maps to raw metric insert.
  - `get_metrics` still returns API-compatible shape.

### 4) Monitoring Agent Changes (`agent/monitor.py`)
- Removed random metric generation logic.
- Added batch processor behavior:
  - Waits for `window_size` raw rows.
  - Computes `mean/min/max/std_dev`.
  - Performs anomaly and threshold checks.
  - Creates alerts.
  - Writes processed batch records and clears raw buffer.
- `GET /agent/status` now reports:
  - running state
  - window size
  - batches processed
  - current raw metric count
  - active alerts

### 5) Collector Added (`metrics_collector.py`)
- New standalone collector script that reads:
  - CPU percent
  - Memory percent
  - Disk usage percent
- Uses `psutil`, writes to `raw_metrics`, logs every sample.

### 6) Dashboard Changes (`dashboard/app.py`)
- `/dashboard` now returns `processed_metrics` + alerts + stats + events.
- `/dashboard/metrics-summary` now summarizes processed batches instead of raw samples.

### 7) API Additions (`main.py`)
- Added threshold management endpoints:
  - `GET /thresholds`
  - `PUT /thresholds/{metric}`
- Fixed root endpoint response typing (`Dict[str, Any]`) to avoid runtime validation issues.

### 8) Alert Manager Improvement (`alerting/alerts.py`)
- `create_alert` now accepts both enum and plain string levels safely.

### 9) Runtime Scripts Added
- `run_collector.sh` -> starts collector process.
- `run_monitoring.sh` -> starts FastAPI service.
- `run_dev.sh` retained.

### 10) Dependency Updates
- Added `psutil>=5.9.0` in `requirements.txt`.

### 11) Cleanup / Repository Hygiene
- Removed generated/unwanted artifacts:
  - `__pycache__` compiled bytecode files
  - local `monitoring.db` artifact from repository
- Added `.gitignore` entries for:
  - Python cache files
  - local DB files
  - virtual environment
  - local env and coverage files

### 12) Documentation Update
- `README.md` updated to include:
  - architecture
  - data flow
  - implementation approach
  - endpoint behavior
  - operational scenarios and troubleshooting

