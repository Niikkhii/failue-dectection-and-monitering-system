import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def fetch_json(path: str):
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=5)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:
        return None, str(exc)


def health_color(status: str) -> str:
    status = (status or "").lower()
    if status == "critical":
        return "#ef4444"
    if status == "warning":
        return "#f59e0b"
    return "#22c55e"


st.set_page_config(page_title="Monitoring Dashboard", layout="wide")
st.title("Failure Detection and Monitoring Dashboard")
st.caption(f"API: {API_BASE_URL}")

left, right = st.columns([3, 1])
with left:
    st.markdown("Live dashboard for health, alerts, and processed metric summaries.")
with right:
    if st.button("Refresh"):
        st.rerun()

health, health_err = fetch_json("/dashboard/health")
agent, agent_err = fetch_json("/agent/status")
summary, summary_err = fetch_json("/dashboard/metrics-summary")
alerts, alerts_err = fetch_json("/alerts/active")

if health_err or agent_err or summary_err or alerts_err:
    st.error("One or more API calls failed. Ensure FastAPI is running.")
    if health_err:
        st.write(f"/dashboard/health error: {health_err}")
    if agent_err:
        st.write(f"/agent/status error: {agent_err}")
    if summary_err:
        st.write(f"/dashboard/metrics-summary error: {summary_err}")
    if alerts_err:
        st.write(f"/alerts/active error: {alerts_err}")
    st.stop()

status = health.get("status", "unknown")
status_col, critical_col, warning_col, active_col = st.columns(4)
status_col.metric("System Status", status.upper())
critical_col.metric("Critical Alerts", health.get("critical_alerts", 0))
warning_col.metric("Warning Alerts", health.get("warning_alerts", 0))
active_col.metric("Active Alerts", health.get("active_alerts", 0))

st.markdown(
    f"<div style='height:6px;background:{health_color(status)};border-radius:6px;'></div>",
    unsafe_allow_html=True,
)
st.write("")

agent_cols = st.columns(4)
agent_cols[0].metric("Agent Running", "Yes" if agent.get("is_running") else "No")
agent_cols[1].metric("Raw Queue Count", agent.get("raw_metrics_count", 0))
agent_cols[2].metric("Batches Processed", agent.get("batches_processed", 0))
agent_cols[3].metric("Window Size", agent.get("window_size", 0))

st.subheader("Processed Metrics Summary")
if not summary:
    st.info("No processed batch data yet. Wait for enough raw samples to build a batch.")
else:
    table_rows = []
    for metric, values in summary.items():
        table_rows.append(
            {
                "metric": metric,
                "batches": values.get("batches", 0),
                "anomalies": values.get("anomalies", 0),
                "overall_mean": round(values.get("overall_mean", 0), 2),
                "overall_min": round(values.get("overall_min", 0), 2),
                "overall_max": round(values.get("overall_max", 0), 2),
            }
        )
    df_summary = pd.DataFrame(table_rows)
    st.dataframe(df_summary, use_container_width=True)

    chart_df = df_summary.set_index("metric")[["overall_mean", "overall_min", "overall_max"]]
    st.bar_chart(chart_df)

st.subheader("Active Alerts")
if not alerts:
    st.success("No active alerts.")
else:
    alerts_df = pd.DataFrame(alerts)
    if "timestamp" in alerts_df.columns:
        alerts_df["timestamp"] = pd.to_datetime(alerts_df["timestamp"], errors="coerce")
        alerts_df = alerts_df.sort_values(by="timestamp", ascending=False)
    st.dataframe(alerts_df, use_container_width=True)

st.caption(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
