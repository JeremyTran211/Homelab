"""
Homelab dashboard: Pi health from monitoring/metrics.db and app status from /srv/status/*.json.

Run locally:
    METRICS_DB=../monitoring/metrics.db STATUS_DIR=/tmp/status uvicorn main:app --reload
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates

from health_check import evaluate  # same thresholds as monitoring/health_check.py

METRICS_DB = os.getenv("METRICS_DB", "/data/metrics.db")
STATUS_DIR = Path(os.getenv("STATUS_DIR", "/status"))

# metrics.py runs every 5 minutes; no new reading for this long means monitoring has stopped
STALE_AFTER_MINUTES = 15

app = FastAPI(title="Homelab dashboard")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def query(sql, params=()):
    """Run a read-only query against metrics.db. Returns a list of dicts, or None if the DB is missing."""
    if not os.path.exists(METRICS_DB):
        return None
    conn = sqlite3.connect(f"file:{METRICS_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, params)]
    finally:
        conn.close()


def minutes_ago(timestamp):
    then = datetime.fromisoformat(timestamp)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - then).total_seconds() // 60)


def ago_text(minutes):
    if minutes < 60:
        return f"{minutes} min ago"
    if minutes < 48 * 60:
        return f"{minutes // 60} h ago"
    return f"{minutes // 1440} days ago"


def get_health():
    rows = query("SELECT * FROM readings ORDER BY id DESC LIMIT 1")
    if not rows:
        return {"status": "NO DATA", "warnings": ["No readings in metrics.db yet"], "reading": None}

    reading = rows[0]
    status, warnings = evaluate(reading)
    age = minutes_ago(reading["timestamp"])
    if age >= STALE_AFTER_MINUTES:
        status = "STALE"
        warnings.append(f"Last reading was {age} minutes ago; is the monitoring cron job running?")
    return {"status": status, "warnings": warnings, "reading": reading, "ago": ago_text(age)}


def get_apps():
    """One entry per <app>.json file in STATUS_DIR, written by each app after it runs."""
    apps = []
    if not STATUS_DIR.is_dir():
        return apps
    for path in sorted(STATUS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            apps.append({"app": path.stem, "ok": False, "error": f"Unreadable status file: {e}"})
            continue
        data.setdefault("app", path.stem)
        data["ok"] = data.get("exit_code") == 0 and data.get("s3_upload", "ok") != "failed"
        if data.get("last_run"):
            data["ago"] = ago_text(minutes_ago(data["last_run"]))
        apps.append(data)
    return apps


@app.get("/api/health")
def api_health():
    """Latest Pi reading and its OK / WARNING / STALE status."""
    return get_health()


@app.get("/api/metrics")
def api_metrics(hours: int = Query(24, ge=1, le=168)):
    """Readings from the last `hours` hours, oldest first."""
    # Timestamps are stored as ISO text ("2026-10-30T06:16:57+00:00"), so compare in the same format
    rows = query(
        "SELECT * FROM readings WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%S', 'now', ?) ORDER BY id",
        (f"-{hours} hours",),
    )
    return {"hours": hours, "readings": rows or []}


@app.get("/api/apps")
def api_apps():
    """Last run of each app that reports to STATUS_DIR."""
    return {"apps": get_apps()}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"health": get_health(), "apps": get_apps()}
    )
