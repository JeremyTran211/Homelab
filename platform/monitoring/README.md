# monitoring

Basic health monitoring for the Pi.

- `metrics.py` records CPU %, memory %, disk % and SoC temperature into `metrics.db` (SQLite). cron runs it every 5 minutes (see [hosts/pi/crontab](../../hosts/pi/crontab)).
- `health_check.py` prints the latest reading and `OK`/`WARNING` against thresholds (CPU 85%, memory 85%, disk 90%, temperature 70°C).

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python metrics.py
.venv/bin/python health_check.py
```

`metrics.db` sits next to the scripts (override with `METRICS_DB=/path/to.db`) and is gitignored.
The data here is what the dashboard, alerts and charts phases of the [roadmap](../../docs/roadmap.md) build on.
