"""
alerts.py — checks the Pi's health and each app's last run, and sends a Discord
message when something needs attention.

Reads the readings and app_runs tables in metrics.db and writes only its own
alert_state table, so a problem is reported once rather than every time this runs.

Run manually (prints what it would send, sends nothing):
    python3 alerts.py --dry-run

Run on a schedule (Pi host, not in Docker): see pi.crontab

Needs DISCORD_WEBHOOK_URL in /srv/homelab/.env, which is never committed.
Standard library only, so it runs on the Pi's system Python.
"""

import json
import os
import socket
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from health_check import CPU_WARN, DISK_WARN, MEM_WARN, TEMP_WARN_C

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("METRICS_DB", os.path.join(HERE, "metrics.db"))
ENV_PATH = os.getenv("HOMELAB_ENV", os.path.join(os.path.dirname(HERE), ".env"))
HOST = socket.gethostname()

# A problem that stays unfixed is repeated this often, so it isn't forgotten
RENOTIFY_HOURS = 24

# metrics.py runs every 5 minutes, so this long without a reading means it stopped
METRICS_STALE_MINUTES = 15

# A run that started this long ago and never finished was interrupted
RUN_STUCK_HOURS = 6

# What counts as a problem for each app. Add a block when you host a new one.
APPS = {
    "scheduler-tdc": {
        # Its run.sh documents these: 0 ok, 1 failed, 2 hours not scheduled.
        # 2 is a normal outcome, so it must not raise an alert.
        "ok_exit_codes": (0, 2),
        # Runs weekly on Wednesdays; 8 days leaves room for a late run
        "max_days_between_runs": 8,
    },
}

# Checks against the latest reading: key, label, column, threshold, unit.
# The thresholds come from health_check.py so the dashboard and these alerts agree.
HEALTH_CHECKS = (
    ("cpu", "CPU", "cpu_percent", CPU_WARN, "%"),
    ("memory", "Memory", "mem_percent", MEM_WARN, "%"),
    ("disk", "Disk", "disk_percent", DISK_WARN, "%"),
    ("temperature", "Temperature", "temp_c", TEMP_WARN_C, "C"),
)


def now():
    return datetime.now(timezone.utc)


def parse_time(value):
    """Timestamps are stored in UTC; treat an unmarked one as UTC rather than local."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def describe(seconds):
    seconds = int(seconds)
    if seconds < 90:
        return f"{seconds} seconds"
    if seconds < 5400:
        return f"{seconds // 60} minutes"
    if seconds < 172800:
        return f"{seconds // 3600} hours"
    return f"{seconds // 86400} days"


def fetch(conn, sql, params=()):
    """Returns [] if the table doesn't exist yet, so a fresh Pi doesn't crash this."""
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise


def check(key, firing, problem, recovered):
    return {"key": key, "firing": firing, "problem": problem, "recovered": recovered}


def check_health(conn):
    rows = fetch(conn, "SELECT * FROM readings ORDER BY id DESC LIMIT 1")
    if not rows:
        return [check("metrics-stale", True, "no readings have ever been recorded", "")]

    row = rows[0]
    age = (now() - parse_time(row["timestamp"])).total_seconds()
    stale = age > METRICS_STALE_MINUTES * 60
    checks = [
        check(
            "metrics-stale",
            stale,
            f"metrics have stopped updating — last reading {describe(age)} ago",
            "metrics are updating again",
        )
    ]
    # An old reading says nothing about the Pi right now, so don't judge it on one
    if stale:
        return checks

    for key, label, column, threshold, unit in HEALTH_CHECKS:
        value = row[column]
        if value is None:
            continue  # temperature is unavailable off the Pi
        checks.append(
            check(
                f"health-{key}",
                value >= threshold,
                f"{label} high: {value:.1f}{unit} (warns at {threshold:.0f}{unit})",
                f"{label} back to normal: {value:.1f}{unit}",
            )
        )
    return checks


def check_apps(conn):
    checks = []
    for app, rules in APPS.items():
        rows = fetch(conn, "SELECT * FROM app_runs WHERE app = ? ORDER BY id DESC LIMIT 1", (app,))
        if not rows:
            continue  # it has never run, so there is nothing to judge yet

        row = rows[0]
        age = (now() - parse_time(row["started_at"])).total_seconds()
        unfinished = row["finished_at"] is None

        checks.append(
            check(
                f"app-{app}-stuck",
                unfinished and age > RUN_STUCK_HOURS * 3600,
                f"{app} started {describe(age)} ago and never finished",
                f"{app} is finishing its runs again",
            )
        )
        checks.append(
            check(
                f"app-{app}-failed",
                not unfinished and row["exit_code"] not in rules["ok_exit_codes"],
                f"{app} failed with exit code {row['exit_code']}",
                f"{app} ran successfully again",
            )
        )
        checks.append(
            check(
                f"app-{app}-overdue",
                age > rules["max_days_between_runs"] * 86400,
                f"{app} has not run in {describe(age)}",
                f"{app} is running on schedule again",
            )
        )
    return checks


def decide(conn, checks):
    """Turns the checks into the messages worth sending, given what was already said."""
    state = {row["key"]: row for row in fetch(conn, "SELECT * FROM alert_state")}
    messages = []

    for item in checks:
        previous = state.get(item["key"])
        was_firing = bool(previous["firing"]) if previous else False

        if item["firing"]:
            if not was_firing:
                messages.append((item["key"], 1, f"🔴 **{HOST}** — {item['problem']}"))
            elif (now() - parse_time(previous["last_sent_at"])).total_seconds() > RENOTIFY_HOURS * 3600:
                messages.append((item["key"], 1, f"🔴 **{HOST}** — still unresolved: {item['problem']}"))
        elif was_firing:
            messages.append((item["key"], 0, f"🟢 **{HOST}** — {item['recovered']}"))

    return messages


def read_webhook_url():
    """Environment first, then .env. Reads only this one key, so an unrelated value
    with quotes or special characters elsewhere in the file can't break it."""
    value = os.getenv("DISCORD_WEBHOOK_URL")
    if value:
        return value
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISCORD_WEBHOOK_URL="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        return None
    return None


def send(webhook_url, content):
    body = json.dumps({"content": content}).encode()
    request = urllib.request.Request(webhook_url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status


def main():
    dry_run = "--dry-run" in sys.argv[1:]

    if not os.path.exists(DB_PATH):
        print(f"alerts: no database at {DB_PATH}. Run metrics.py first.", file=sys.stderr)
        sys.exit(1)

    webhook_url = read_webhook_url()
    if not webhook_url and not dry_run:
        print(f"alerts: DISCORD_WEBHOOK_URL is not set in {ENV_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_state (
                key TEXT PRIMARY KEY,
                firing INTEGER NOT NULL,
                last_sent_at TEXT NOT NULL
            )
            """
        )

    messages = decide(conn, check_health(conn) + check_apps(conn))
    if not messages:
        print("Nothing to report.")
        conn.close()
        return

    failures = 0
    for key, firing, content in messages:
        if dry_run:
            print(f"WOULD SEND: {content}")
            continue
        try:
            send(webhook_url, content)
        except (urllib.error.URLError, OSError) as e:
            # Leave this alert's state alone so the next run tries again
            print(f"alerts: could not send {key}: {e}", file=sys.stderr)
            failures += 1
            continue
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO alert_state (key, firing, last_sent_at) VALUES (?, ?, ?)",
                (key, firing, now().isoformat()),
            )
        print(f"Sent: {content}")

    conn.close()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
