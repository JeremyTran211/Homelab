"""
health_check.py — reads the most recent metrics snapshot from metrics.db
and prints an overall health status.

Run manually:
    python3 health_check.py
"""

import os
import sqlite3
import sys

# Stored next to this script unless METRICS_DB is set, so cron can run it from anywhere
DB_PATH = os.getenv("METRICS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics.db"))

# Tune these to whatever makes sense for chocochip
CPU_WARN = 85.0
MEM_WARN = 85.0
DISK_WARN = 90.0
TEMP_WARN_C = 70.0  # Pi typically starts throttling around 80C


def get_latest_reading(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM readings ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row


def evaluate(row):
    """Returns (overall_status, list_of_warning_strings)."""
    warnings = []

    if row["cpu_percent"] >= CPU_WARN:
        warnings.append(f"CPU high: {row['cpu_percent']:.1f}%")
    if row["mem_percent"] >= MEM_WARN:
        warnings.append(f"Memory high: {row['mem_percent']:.1f}%")
    if row["disk_percent"] >= DISK_WARN:
        warnings.append(f"Disk high: {row['disk_percent']:.1f}%")
    if row["temp_c"] is not None and row["temp_c"] >= TEMP_WARN_C:
        warnings.append(f"Temp high: {row['temp_c']:.1f}C")

    status = "WARNING" if warnings else "OK"
    return status, warnings


def main():
    row = get_latest_reading()
    if row is None:
        print("No metrics recorded yet. Run metrics.py first.")
        sys.exit(1)

    status, warnings = evaluate(row)
    temp_display = f"{row['temp_c']:.1f}C" if row["temp_c"] is not None else "N/A"

    print(f"Last reading: {row['timestamp']}")
    print(
        f"CPU: {row['cpu_percent']:.1f}% | "
        f"MEM: {row['mem_percent']:.1f}% | "
        f"DISK: {row['disk_percent']:.1f}% | "
        f"TEMP: {temp_display}"
    )
    print(f"Status: {status}")
    for w in warnings:
        print(f"  - {w}")


if __name__ == "__main__":
    main()
