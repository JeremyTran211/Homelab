# Homelab

A hybrid on-prem + AWS homelab. It provides the infrastructure that apps and sites
run on: the machines, shared services, scheduling, monitoring, and the AWS pieces that
connect it all to the internet. It's built to learn Docker, Linux, automation and AWS, together.

This repo holds **infrastructure only**. Each app or site lives in its own repo and is
deployed onto the lab as described in [docs/hosting-an-app.md](docs/hosting-an-app.md).

## Hosts

| Host | Role | Status |
|---|---|---|
| [chocochip](hosts/pi/) (Raspberry Pi) | Runs everything today | Live |
| [nuc12](hosts/nuc12/) (Intel NUC12) | Heavier services and sites | Planned |

## What's running

| Service | Kind | Where | Repo |
|---|---|---|---|
| Health monitoring | Platform | Pi, cron every 5 min | [platform/monitoring](platform/monitoring/) |
| Scheduler_TDC | App | Pi, Docker, cron every Wednesday | [JeremyTran211/Scheduler_TDC](https://github.com/JeremyTran211/Scheduler_TDC) |
| S3 + IAM | Cloud | AWS us-east-1 | [cloud/aws](cloud/aws/) |

## Repo layout

```
hosts/       per-machine config: crontab, folder layout, setup notes
platform/    shared services: monitoring, and later a reverse proxy, database, dashboards
cloud/aws/   AWS resources and IAM policies
docs/        architecture, roadmap, security, setup log, runbooks
```

## Rules

- Secrets never go in git. Real `.env` files and keys live only on the hosts.
- Changes go through a branch and a pull request, so the other person can review.
- Anything changed by hand on a host gets a line in [docs/setup-log.md](docs/setup-log.md).

## Docs

- [Architecture](docs/architecture.md): how the pieces connect
- [Hosting an app](docs/hosting-an-app.md): how an app repo gets deployed onto the lab
- [Roadmap](docs/roadmap.md): what's done and what's next
- [Security](docs/security.md): secrets and AWS access
- [Setup log](docs/setup-log.md): dated journal of changes
- [Runbook: set up the Pi from these repos](docs/runbooks/pi-migration.md)
