# Failure Detection Monitoring System

A lightweight FastAPI-based monitoring system that continuously collects synthetic system metrics, detects anomalies and threshold breaches, raises alerts, and exposes dashboard-style APIs for observability.

## 1) Project Purpose

This project demonstrates an end-to-end monitoring pipeline:
- Collect runtime metrics periodically.
- Detect abnormal behavior and threshold violations.
- Generate and track alerts.
- Provide health, status, and summary APIs for dashboards or integrations.

It is useful as:
- A learning project for monitoring/alerting fundamentals.
- A base template for adding real infrastructure metrics.
- A backend API for a monitoring dashboard UI.

## 2) High-Level Architecture

Core modules:
- `main.py` - FastAPI app, API routes, startup/shutdown lifecycle.
- `agent/monitor.py` - Background monitoring agent and metric collection loop.
- `detector/engine.py` - Threshold checks and anomaly detection logic.
- `alerting/alerts.py` - In-memory alert management and stats.
- `storage/database.py` - SQLite persistence for metrics/events (and alert table schema).
- `dashboard/app.py` - Dashboard aggregation APIs (`/dashboard*`).

Data flow:
1. App starts (`startup` event in `main.py`).
2. Background agent (`MonitoringAgent`) begins collecting metrics every 5 seconds.
3. Each metric is persisted to SQLite (`metrics` table).
4. Detection engine evaluates:
   - Statistical anomalies (window-based deviation),
   - Threshold violations (`cpu`, `memory`, `disk`, `error_rate`).
5. Alert manager creates in-memory alerts when issues are found.
6. Dashboard/service endpoints expose metrics, alerts, and health summaries.

## 3) Runtime Components and Responsibilities

### 3.1 Monitoring Agent (`agent/monitor.py`)

Responsibilities:
- Runs asynchronous loop while `is_running=True`.
- Generates synthetic metrics:
  - `cpu`
  - `memory`
  - `disk`
  - `error_rate`
- Stores each sample in database.
- Maintains `metrics_history` in memory for anomaly detection.
- Creates events (`metrics_collected`) in database.

Effect on system:
- Drives all observable data in dashboard and summary endpoints.
- If this agent stops, metric data and new alerts stop updating.

### 3.2 Detection Engine (`detector/engine.py`)

Responsibilities:
- `check_metric(metric_name, value)`:
  - Compares values against threshold map.
  - Emits warning/critical alert candidates.
- `detect_anomaly(metrics, window=10)`:
  - Computes moving average and std dev over recent values.
  - Flags latest sample if > 2 standard deviations away.

Default threshold map:
- `cpu`: 80.0
- `memory`: 85.0
- `disk`: 90.0
- `error_rate`: 5.0

Effect on system:
- A stricter threshold produces more alerts.
- A wider metric range increases anomaly probability.
- If history length < window, anomaly detection does not trigger.

### 3.3 Alert Manager (`alerting/alerts.py`)

Responsibilities:
- Stores alerts in memory list.
- Returns active/unresolved/all alerts.
- Resolves alerts and tracks simple stats.
- Supports subscriber callbacks.

Important behavior:
- Alerts are currently in memory (not persisted by AlertManager).
- Restarting app resets in-memory alerts and stats.

Effect on system:
- Dashboard health status depends on unresolved alert counts.
- More active critical alerts -> status transitions to `critical`.

### 3.4 Database Layer (`storage/database.py`)

SQLite tables:
- `metrics(id, timestamp, name, value, tags)`
- `alerts(id, timestamp, level, message, resolved)`
- `events(id, timestamp, event_type, data)`

Current usage:
- Metrics and events are actively written and read.
- In-memory alert manager is primary source for API alert responses.
- `alerts` table schema exists for extension/future persistence alignment.

Effect on system:
- DB growth directly affects response payload size for endpoints reading large limits.
- DB lock/corruption issues can break ingestion and dashboard freshness.

### 3.5 Dashboard Service (`dashboard/app.py`)

Responsibilities:
- `/dashboard` -> aggregate metrics + alerts + stats + events.
- `/dashboard/metrics-summary` -> grouped counts and min/max/avg per metric.
- `/dashboard/health` -> health status from active warning/critical alerts.

Effect on system:
- It is the primary “operator view” layer for current project.
- If no alerts are active, health status reports `healthy`.

## 4) API Endpoint Reference

### 4.1 Core health and root
- `GET /health`
  - Quick service-level health check.
  - Returns `{"status": "healthy", "service": "monitoring-system"}`.
- `GET /`
  - Service metadata + quick endpoint index.
  - Useful as lightweight entrypoint sanity check.

### 4.2 Metrics
- `GET /metrics?limit=100`
  - Returns most recent metrics from DB.
- `POST /metrics`
  - Insert external/custom metric record.
  - Body:
    - `name: str`
    - `value: float`
    - `tags: Optional[str]`

### 4.3 Alerts
- `GET /alerts?limit=50`
- `GET /alerts/active`
- `POST /alerts`
  - Body:
    - `level: str` (`info|warning|critical`)
    - `message: str`
    - `source: Optional[str]`
- `PUT /alerts/{alert_id}/resolve`
- `GET /alerts/stats`

### 4.4 Dashboard
- `GET /dashboard`
- `GET /dashboard/metrics-summary`
- `GET /dashboard/health`

### 4.5 Agent
- `GET /agent/status`
  - Reports:
    - `is_running`
    - `metrics_tracked`
    - `active_alerts`

## 5) What Affects What (Cause -> Effect Map)

- Agent stopped -> No new metrics/events -> Dashboard data becomes stale.
- DB write failure -> Missing metrics/events -> Summaries incomplete or static.
- Threshold lowered (e.g., CPU 80 -> 60) -> More warning/critical alerts.
- Threshold raised (e.g., CPU 80 -> 95) -> Fewer threshold-based alerts.
- High metric volatility -> More anomaly alerts (std-dev rule).
- Many unresolved critical alerts -> `/dashboard/health` becomes `critical`.
- Alerts resolved -> Active count decreases -> Health may recover to `warning` or `healthy`.
- App restart -> In-memory alerts reset -> Health can appear improved until new alerts occur.

## 6) Scenario Type Descriptions (Operational Cases)

### Case A: Normal steady state
Symptoms:
- `/dashboard/health` => `healthy`
- `/agent/status` => `is_running: true`
- `/dashboard/metrics-summary` shows ongoing values
Interpretation:
- Ingestion and analysis pipeline is functioning.

### Case B: Threshold pressure
Symptoms:
- Active warnings/criticals increase
- Alert messages mention threshold exceeded
Interpretation:
- One or more metrics are beyond configured risk limits.
Action:
- Investigate metric source, tune threshold if needed.

### Case C: Anomaly spike without threshold breach
Symptoms:
- Warning alerts for anomaly detected
- Metric may still be under absolute threshold
Interpretation:
- Sudden behavior change relative to recent baseline.
Action:
- Check upstream deployment/events around that timestamp.

### Case D: Agent failure or inactivity
Symptoms:
- `/agent/status` indicates not running
- Metrics count in summary stops changing
Interpretation:
- Background collector is not active.
Action:
- Restart service and inspect startup logs.

### Case E: Data-layer issue
Symptoms:
- Endpoint errors on metric/event reads or writes
- Dashboard partially populated or stale
Interpretation:
- SQLite file lock/path/permission issue.
Action:
- Validate DB path, file permissions, and active process locks.

### Case F: Root endpoint failure
Symptoms:
- `GET /` returns 500 while other endpoints work.
Interpretation:
- Route-level typing/serialization bug, not full service outage.
Action:
- Fix route response model/type hints (already fixed in this repo).

## 7) Setup and Run

Prerequisites:
- Python 3.13 (recommended in this project environment).
- macOS/Linux shell compatible with bash script.

Install:
1. `cd /Users/nikhilcharantimath/Desktop/failure_detction/monitoring-system`
2. `python3 -m venv venv` (if not already created)
3. `./venv/bin/pip install -r requirements.txt`

Run (recommended):
- `./run_dev.sh`

Alternative run:
- `./venv/bin/uvicorn main:app --reload`

Open docs:
- `http://127.0.0.1:8000/docs`

Stop:
- `Ctrl + C`

## 8) Smoke Test Checklist

Expected 200 responses:
- `GET /dashboard`
- `GET /dashboard/health`
- `GET /agent/status`
- `GET /dashboard/metrics-summary`
- `GET /`

If `GET /` fails, verify latest code is running and app reloaded.

## 9) Current Design Trade-offs and Limitations

- Alerts are in memory; they do not survive restart.
- Metrics are synthetic/random, not pulled from real host telemetry.
- No auth/rate limits; API is open by default.
- No distributed processing (single-process app).
- Basic anomaly logic (2 std dev rule) may produce false positives/negatives.
- `metrics-summary` returns raw values list, which can grow large.

## 10) Suggested Next Improvements

- Persist alerts to SQLite and reconcile with `alerts` table.
- Add real metric collectors (CPU/memory/disk from host or exporters).
- Add configurable threshold APIs and persistent configuration.
- Add authentication and role-based API access.
- Add pruning/retention policies for DB growth.
- Add automated tests (unit + API integration).
- Add structured logging and tracing for production diagnostics.

## 11) Quick Troubleshooting Guide

- Error: `zsh: no such file or directory: venv/bin/uvicorn`
  - Cause: command executed outside project directory.
  - Fix: run `./run_dev.sh` or use absolute path to script.

- Error: dependency install fails on old pinned versions
  - Cause: Python 3.13 incompatibility with very old wheel versions.
  - Fix: use current `requirements.txt` (already updated).

- Endpoint returns 500
  - Check uvicorn console traceback first.
  - Validate route return types and serialization compatibility.
  - Confirm database file and permissions are valid.

---

For demos/reports, focus on this narrative:
1. Agent continuously ingests metrics.
2. Detection engine transforms raw metrics into actionable alert signals.
3. Dashboard endpoints convert system internals into operator-facing status and summaries.
