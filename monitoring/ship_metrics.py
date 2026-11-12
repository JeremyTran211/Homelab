"""
ship_metrics.py — copies readings from metrics.db to AWS CloudWatch, so the Pi's
health is visible off-site. That lets an alarm notice when the Pi stops reporting,
which alerts.py can never do: if the Pi dies, it dies too.

Run manually (shows what it would send, sends nothing):
    .venv/bin/python ship_metrics.py --dry-run

Run on a schedule (Pi host, not in Docker): see pi.crontab

Uses the "homelab" AWS profile, kept separate from any app's credentials.
Needs boto3: .venv/bin/pip install -r requirements.txt
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("METRICS_DB", os.path.join(HERE, "metrics.db"))

# Groups these metrics in the CloudWatch console. The IAM policy in
# aws/pi-cloudwatch-policy.json allows writing to this namespace and no other.
NAMESPACE = "Homelab"

# A profile of its own, so the Pi's platform credentials are never an app's
AWS_PROFILE = os.getenv("AWS_PROFILE", "homelab")
AWS_REGION = os.getenv("AWS_REGION")  # falls back to the profile's own region

# Each reading becomes this many data points. One call carries up to 20 of them.
READINGS_PER_CALL = 5

# CloudWatch refuses anything older than two weeks, and one bad point fails the
# whole call, so skip old rows rather than get stuck retrying them forever.
MAX_AGE_DAYS = 13

# Column -> CloudWatch metric name and unit
METRICS = (
    ("cpu_percent", "CPUPercent", "Percent"),
    ("mem_percent", "MemoryPercent", "Percent"),
    ("disk_percent", "DiskPercent", "Percent"),
    ("temp_c", "TemperatureC", "None"),
)


def parse_time(value):
    """Timestamps are stored in UTC; treat an unmarked one as UTC, not local."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def cloudwatch_client():
    """Imported here rather than at the top so --dry-run works without boto3."""
    try:
        import boto3
    except ImportError:
        print(
            "ship_metrics: boto3 is not installed. Run:\n"
            "  cd /srv/homelab/monitoring && .venv/bin/pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client("cloudwatch", region_name=AWS_REGION) if AWS_REGION else session.client("cloudwatch")


def datums_for(row, host):
    """Turns one reading into CloudWatch data points, one per metric."""
    timestamp = parse_time(row["timestamp"])
    points = []
    for column, name, unit in METRICS:
        value = row[column]
        if value is None:
            continue  # temperature is unavailable off the Pi
        points.append(
            {
                "MetricName": name,
                "Dimensions": [{"Name": "Host", "Value": host}],
                "Timestamp": timestamp,
                "Value": float(value),
                "Unit": unit,
            }
        )
    return points


def main():
    dry_run = "--dry-run" in sys.argv[1:]

    if not os.path.exists(DB_PATH):
        print(f"ship_metrics: no database at {DB_PATH}. Run metrics.py first.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shipping_state (
                name TEXT PRIMARY KEY,
                last_id INTEGER NOT NULL
            )
            """
        )

    state = conn.execute("SELECT last_id FROM shipping_state WHERE name = 'cloudwatch'").fetchone()
    last_id = state["last_id"] if state else 0

    rows = conn.execute("SELECT * FROM readings WHERE id > ? ORDER BY id", (last_id,)).fetchall()
    if not rows:
        print(f"Nothing new to ship (already sent up to reading {last_id}).")
        conn.close()
        return

    # The host name is recorded on the Pi, so the metric says which machine it came from
    host = os.getenv("METRICS_HOST") or os.uname().nodename
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    client = None
    sent = skipped = 0

    for batch in chunks(rows, READINGS_PER_CALL):
        datums = []
        for row in batch:
            if parse_time(row["timestamp"]) < cutoff:
                skipped += 1
                continue  # too old for CloudWatch to accept
            datums.extend(datums_for(row, host))

        highest_id = batch[-1]["id"]

        if datums:
            if dry_run:
                print(f"WOULD SEND {len(datums)} data points, up to reading {highest_id}")
            else:
                if client is None:
                    client = cloudwatch_client()
                try:
                    client.put_metric_data(Namespace=NAMESPACE, MetricData=datums)
                except Exception as e:
                    # boto3 raises a different type for credentials, network and
                    # throttling problems; the answer is the same for all of them.
                    # The marker stays put, so the next run picks up from here.
                    print(f"ship_metrics: could not send readings up to {highest_id}: {e}", file=sys.stderr)
                    conn.close()
                    sys.exit(1)
            sent += len(datums)

        # Record progress per call, so a later failure doesn't re-send what landed
        if not dry_run:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO shipping_state (name, last_id) VALUES ('cloudwatch', ?)",
                    (highest_id,),
                )

    conn.close()
    verb = "Would ship" if dry_run else "Shipped"
    note = f", skipped {skipped} reading(s) older than {MAX_AGE_DAYS} days" if skipped else ""
    print(f"{verb} {sent} data points from {len(rows)} reading(s) as {host}{note}.")


if __name__ == "__main__":
    main()
