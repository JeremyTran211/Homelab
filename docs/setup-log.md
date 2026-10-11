# Setup log

A dated record of changes, newest first. Anything done by hand on a host goes here.
Scheduler_TDC's history before Oct 2026 is in [its own repo](https://github.com/JeremyTran211/Scheduler_TDC/commits/main).

| Date | Change |
|---|---|
| 2026-10-11 | Split into an infra repo (this one) and app repos. Repos move to `/srv/homelab` and `/srv/apps/<app>` on the Pi. |
| 2026-10-11 | Pi's AWS key was failing (`InvalidClientTokenId`), so the Oct 9 scheduler logs never reached S3. Fixed by re-running `aws configure`; root cause unknown. Confirmed it's a dedicated `scheduler-tdc-uploader` user, scoped to the bucket. |
| 2026-10-11 | Scheduler moves from the 3-week Wed/Thu/Fri rotation to every Wednesday. Crontab gets a `PATH` so cron can find `aws`. |
| 2026-10-04 | Scheduler run script and the Pi health metrics scripts committed to Scheduler_TDC. |
| 2026-08-28 | Started `metrics.py` on the Pi every 5 minutes (SQLite). |
| 2026-08-26 | First scheduler logs uploaded to S3. |
| 2026-07-29 | Scheduler fully Dockerized on the Pi. |
| 2026-07-01 | Pi running the scheduler headless via cron. |
| 2026-06-28 | Homelab repo created. |
