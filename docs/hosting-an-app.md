# Hosting an app on the homelab

Apps and sites live in their own repos. This repo decides **where and when** they run.

## What an app repo provides

| Item | Why |
|---|---|
| A way to run it: a `Dockerfile` + `docker-compose.yml`, and a `run.sh` if it runs on a schedule | The lab runs everything in Docker |
| `.env.example` | Lists the settings it needs, with placeholder values |
| A README | What it does, how to run it, exit codes if cron runs it |
| Works on `linux/arm64` | The Pi is ARM |

The app repo **doesn't** contain hostnames, paths on the Pi, cron schedules, or real secrets.

## What this repo provides

| Item | Where |
|---|---|
| Where it's cloned on the host | `/srv/apps/<app-name>` (see the host's README) |
| When it runs | `hosts/<host>/crontab`, or a long-running service once the reverse proxy exists |
| AWS access, if needed | A dedicated IAM user or role with a scoped policy in `cloud/aws/iam/` |
| How it reaches the internet, if it's a site | Reverse proxy + public edge (roadmap) |

## Adding a new app

1. Make sure the app repo has the items in the first table.
2. On the host: `git clone <repo> /srv/apps/<app-name>`, then `cp .env.example .env` and fill it in.
3. In this repo, open a PR that:
   - adds its schedule to `hosts/<host>/crontab`, or its service to `platform/`
   - adds any IAM policy to `cloud/aws/iam/`
   - adds a row to "What's running" in the README
4. After merging: install the crontab on the host, and add a line to `docs/setup-log.md`.

## Updating an app

```bash
cd /srv/apps/<app-name> && git pull && docker compose build
```

(Automated deploys with GitHub Actions are on the roadmap.)
