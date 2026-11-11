"""
run_app.py — runs an app's command and records when it ran and how it exited
in the app_runs table of metrics.db. The dashboard reads that table.

Usage (see pi.crontab):
    python3 run_app.py <app-name> <command> [args...]

Try it without touching a real app or the real database:
    METRICS_DB=/tmp/test.db python3 run_app.py test-app false

Standard library only, so it runs on the Pi's system Python. The app's output
and working directory are left alone, and this script exits with the app's exit
code. If recording fails, the app still runs: a monitoring problem should never
stop real work.
"""

import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

# Stored next to this script unless METRICS_DB is set, so cron can run it from anywhere
DB_PATH = os.getenv("METRICS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics.db"))


def now():
    return datetime.now(timezone.utc).isoformat()


def warn(message):
    print(f"run_app: {message}", file=sys.stderr)


def record_start(app):
    """Adds a row with no finish time yet. Returns its id, or None if recording failed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    exit_code INTEGER
                )
                """
            )
            run_id = conn.execute(
                "INSERT INTO app_runs (app, started_at) VALUES (?, ?)", (app, now())
            ).lastrowid
        conn.close()
        return run_id
    except sqlite3.Error as e:
        warn(f"could not record start: {e}")
        return None


def record_finish(run_id, exit_code):
    if run_id is None:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        with conn:
            conn.execute(
                "UPDATE app_runs SET finished_at = ?, exit_code = ? WHERE id = ?",
                (now(), exit_code, run_id),
            )
        conn.close()
    except sqlite3.Error as e:
        warn(f"could not record finish: {e}")


def run_command(command):
    """Runs the command and returns its exit code, using the shell's numbering for failures."""
    try:
        code = subprocess.run(command).returncode
    except FileNotFoundError:
        warn(f"command not found: {command[0]}")
        return 127
    except PermissionError:
        warn(f"command not executable: {command[0]}")
        return 126
    # Python reports "killed by signal N" as -N; the shell convention is 128 + N
    return 128 - code if code < 0 else code


def main():
    if len(sys.argv) < 3:
        print("Usage: run_app.py <app-name> <command> [args...]", file=sys.stderr)
        sys.exit(2)

    app, command = sys.argv[1], sys.argv[2:]
    run_id = record_start(app)
    exit_code = run_command(command)
    record_finish(run_id, exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
