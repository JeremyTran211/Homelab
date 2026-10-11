# Roadmap

Phases are done roughly in order, at our own pace. No due dates: this is a side project and
the commit history shows when each piece shipped.

## ✅ Done

- [x] Raspberry Pi running Docker and cron
- [x] First app hosted: Scheduler_TDC (weekly bot, logs and screenshots shipped to S3)
- [x] Pi health metrics (CPU, RAM, disk, temp) every 5 minutes into SQLite, plus a health check
- [x] Dedicated, bucket-scoped IAM user for the Pi ([security.md](security.md))
- [x] Infra and apps split into separate repos ([hosting-an-app.md](hosting-an-app.md))

## Phase 0: Clean start

- [ ] Set up `/srv/homelab` and `/srv/apps/` on the Pi and switch cron over ([runbook](runbooks/pi-migration.md))
- [ ] Collaborator access: GitHub collaborator + branch protection on `main` (PR review required),
      a separate Linux user on the Pi, a separate IAM user in AWS (no shared logins)

## Phase 1: Dashboard

- [ ] FastAPI app showing system health (from metrics.db) and app status (last run, exit code)
- [ ] Run it in Docker on the Pi

## Phase 2: Cloud observability (hybrid)

- [ ] Ship logs and/or custom metrics to CloudWatch, with a log group per service
- [ ] Verify Pi logs appear in AWS
- [ ] Stretch: register the Pi with **SSM as a hybrid managed node**, or use **IAM Roles Anywhere**, to replace long-lived access keys

## Phase 3: Alerts

- [ ] App problems: a scheduled app exited non-zero, or hasn't run successfully when it should have
- [ ] Disk too full, CPU too high, Pi too hot (thresholds already in `health_check.py`)
- [ ] Deliver to Discord, email or SNS

## Phase 4: Reverse proxy

- [ ] Nginx in Docker on the Pi, routing by hostname to the dashboard and sites

## Phase 5: Public edge on AWS + hosted sites

- [ ] Move my domain's DNS to Route 53
- [ ] Small EC2 instance as the public entry point: HTTPS certificates, reverse proxy
- [ ] Encrypted tunnel (WireGuard or Tailscale) from the Pi to the EC2 instance, so no home ports are opened
- [ ] Host my revamped personal site, then a second site, each from its own repo
- [ ] Optional: S3 + CloudFront fallback copy when home is down

## Phase 6: Database and history

- [ ] Postgres in Docker
- [ ] Migrate metrics from SQLite and record why
- [ ] Query historical metrics

## Phase 7: Charts

- [ ] Grafana, or charts in the dashboard: CPU, RAM, disk, uptime over time

## Phase 8: Automated deploys

- [ ] GitHub Actions deploys app repos on merge to `main`
- [ ] Use a **self-hosted runner on the Pi**, or Tailscale, instead of exposing SSH to the internet

## Phase 9: Backups

- [ ] Timestamped backups of databases and `.env` files (encrypted) to S3
- [ ] S3 lifecycle rules to expire old logs and backups
- [ ] Test a restore

## Phase 10: Second host

- [ ] Bring the NUC12 online and move heavier services to it

## Phase 11: Polish

- [ ] README screenshots and a demo video
- [ ] Architecture diagram up to date
- [ ] Write up STAR stories: why we built it, a Docker issue, AWS integration, a monitoring/alerting failure, deployment automation
