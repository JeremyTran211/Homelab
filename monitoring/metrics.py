"""
metrics.py — collects CPU, memory, disk, and temperature and stores
a snapshot in a local SQLite database (metrics.db).

Run manually:
    python3 metrics.py

Run on a schedule (Pi host, not in Docker): see pi.crontab
"""

import os
import sqlite3
from datetime import datetime, timezone

import psutil

# Stored next to this script unless METRICS_DB is set, so cron can run it from anywhere
DB_PATH = os.getenv("METRICS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics.db"))
THERMAL_ZONE_PATH = "/sys/class/thermal/thermal_zone0/temp"


def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_percent REAL NOT NULL,
            mem_percent REAL NOT NULL,
            disk_percent REAL NOT NULL,
            temp_c REAL
        )
        """
    )
    conn.commit()
    return conn


def get_cpu_temp_c():
    """Read SoC temperature. Returns None if unavailable (e.g. not on a Pi)."""
    try:
        with open(THERMAL_ZONE_PATH, "r") as f:
            millidegrees = int(f.read().strip())
        return millidegrees / 1000.0
    except (FileNotFoundError, ValueError):
        return None


def collect_metrics():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "mem_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "temp_c": get_cpu_temp_c(),
    }


def save_metrics(conn, metrics):
    conn.execute(
        """
        INSERT INTO readings (timestamp, cpu_percent, mem_percent, disk_percent, temp_c)
        VALUES (:timestamp, :cpu_percent, :mem_percent, :disk_percent, :temp_c)
        """,
        metrics,
    )
    conn.commit()


def main():
    conn = init_db()
    metrics = collect_metrics()
    save_metrics(conn, metrics)
    conn.close()

    temp_display = f"{metrics['temp_c']:.1f}C" if metrics["temp_c"] is not None else "N/A"
    print(
        f"[{metrics['timestamp']}] "
        f"CPU: {metrics['cpu_percent']:.1f}% | "
        f"MEM: {metrics['mem_percent']:.1f}% | "
        f"DISK: {metrics['disk_percent']:.1f}% | "
        f"TEMP: {temp_display}"
    )


if __name__ == "__main__":
    main()
