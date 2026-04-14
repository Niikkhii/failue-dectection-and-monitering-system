# Failure Detection and Monitoring System

Production-style monitoring backend built with FastAPI, SQLite, and a separate collector process.

## Overview

This project detects unhealthy behavior by collecting real host metrics, processing them in batches, and generating alerts when:
- values cross configured thresholds, or
- values show anomaly-like deviations from recent batch statistics.

It is designed as a learning-to-production bridge:
- simple enough to run locally,
- structured with clear separation of concerns (collector, processor, API, storage, alerting).

## Architecture

### Components

- `metrics_collector.py`
  - Separate process.
  - Collects real metrics (`cpu`, `memory`, `disk`) using `psutil` every 5 seconds.
  - Writes to `raw_metrics`.

- `agent/monitor.py`
  - Background processor running inside FastAPI app lifecycle.
  - Waits until enough raw rows exist (window size = 10).
  - Processes one batch: computes `mean/min/max/std_dev`, checks anomaly + thresholds.
  - Writes results to `processed_metrics`.
  - Creates alerts through `AlertManager`.

- `detector/engine.py`
  - Threshold map and threshold-check logic.
  - Anomaly utility logic.
  - Supports threshold updates.

- `alerting/alerts.py`
  - In-memory alert manager.
  - Tracks active/resolved alerts and aggregate stats.

- `storage/database.py`
  - SQLite schema management.
  - CRUD helpers for raw metrics, processed metrics, events.

- `dashboard/app.py`
  - Aggregates data for dashboard endpoints.

- `main.py`
  - FastAPI app + routes.
  - Starts/stops background processing agent.

## Data Flow (End-to-End)

1. Collector reads real host metrics every 5 seconds.
2. Collector inserts into `raw_metrics`.
3. Monitoring agent polls raw count every 5 seconds.
4. When `raw_count >= window_size (10)`, batch processing triggers.
5. Processor groups by metric type and computes statistics.
6. Processor checks:
   - threshold exceeded -> warning/critical alert
   - anomaly condition -> warning alert
7. Processor writes one record per metric to `processed_metrics`.
8. Processor logs event and clears raw buffer for next batch window.
9. Dashboard endpoints expose processed summaries, status, and alerts.

## Database Schema

### `raw_metrics`
- `id` (PK)
- `timestamp`
- `metric_type`
- `value`
- `server`
- `tags`

### `processed_metrics`
- `id` (PK)
- `batch_timestamp`
- `metric_type`
- `mean`
- `min_value`
- `max_value`
- `std_dev`
- `anomaly_detected`
- `threshold_exceeded`

### `alerts`
- `id` (PK)
- `timestamp`
- `level`
- `message`
- `resolved`

### `events`
- `id` (PK)
- `timestamp`
- `event_type`
- `data`

## API Reference

### Core
- `GET /` - service info + endpoint index
- `GET /health` - API health check

### Metrics
- `GET /metrics?limit=100`
  - Returns recent raw metric rows (compatibility shape).
- `POST /metrics`
  - Insert external/custom metric sample.

### Alerts
- `GET /alerts`
- `GET /alerts/active`
- `POST /alerts`
- `PUT /alerts/{alert_id}/resolve`
- `GET /alerts/stats`

### Dashboard
- `GET /dashboard`
  - Returns latest processed metrics, active alerts, stats, health status, events.
- `GET /dashboard/metrics-summary`
  - Batch-level summary by metric (`batches`, `anomalies`, `overall_mean/min/max`).
- `GET /dashboard/health`
  - Health derived from active alert severity.

### Agent
- `GET /agent/status`
  - `is_running`, `window_size`, `batches_processed`, `raw_metrics_count`, `active_alerts`.

### Thresholds
- `GET /thresholds`
- `PUT /thresholds/{metric}` with body:
  - `{ "value": 75.0 }`

## Cause-and-Effect Map (What Affects What)

- Collector stopped -> raw table stops growing -> no new batch processing.
- Raw rows below window size -> agent waits -> summary remains unchanged.
- High threshold values -> fewer alerts.
- Low threshold values -> more frequent alerts.
- Large sudden metric jump -> anomaly alert likely.
- Critical alerts increase -> `/dashboard/health` shifts to `critical`.
- Resolving alerts -> health can recover to `warning` or `healthy`.
- API restart -> in-memory alert history resets (current design limitation).

## Implementation Approach

The solution uses a two-stage pipeline:

- **Stage 1: Ingestion**
  - fast and lightweight writes (`raw_metrics`) from collector.
- **Stage 2: Analysis**
  - periodic batch processing for stable statistical decisions.

This reduces noisy single-point decisions and mirrors real monitoring system behavior:
- decoupled producer (collector),
- processor with windowed analysis,
- summarized outputs for dashboard/operations.

## Run Instructions

### 1) Setup

```bash
cd /Users/nikhilcharantimath/Desktop/failure_detction/monitoring-system
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2) Start Collector (Terminal 1)

```bash
./run_collector.sh
```

### 3) Start Monitoring API (Terminal 2)

```bash
./run_monitoring.sh
```

### 4) Open Swagger

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Smoke Test Checklist

Expected `200`:
- `GET /`
- `GET /dashboard`
- `GET /dashboard/health`
- `GET /dashboard/metrics-summary`
- `GET /agent/status`

Also verify:
- `raw_metrics_count` increases while collector runs.
- `batches_processed` increments after enough samples are collected.

## Unwanted File Cleanup Done

Removed generated artifacts from repository working tree:
- Python bytecode files under `__pycache__`
- local `monitoring.db`

Added `.gitignore` to prevent re-adding:
- `__pycache__/`
- `*.py[cod]`
- `*.db`
- local environment/cache artifacts

## Current Limitations

- Alerts are in memory only (not persisted across restart).
- SQLite is local-node friendly, not distributed scale.
- No authentication/authorization yet.
- No automated tests/CI yet.
- Collector currently covers host-level metrics only.

## Recommended Next Steps

- Persist alerts and incident correlations to DB.
- Add test suite (unit + API + integration).
- Add auth/rate limiting for APIs.
- Add retention and pruning policy.
- Add deployment profiles (`dev/staging/prod`) with per-environment thresholds.
