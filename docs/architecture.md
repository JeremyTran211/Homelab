# Architecture

## Repos

```mermaid
flowchart LR
    homelab["Homelab repo<br/>hosts, platform, cloud, docs"]
    sched["Scheduler_TDC repo<br/>app"]
    sites["Site repos<br/>(planned)"]
    pi["chocochip<br/>/srv/homelab<br/>/srv/apps/*"]

    homelab -->|"cloned to /srv/homelab<br/>crontab installed from it"| pi
    sched -->|"cloned to /srv/apps/scheduler-tdc"| pi
    sites -.-> pi
```

The Homelab repo defines the platform. Each app repo is cloned under `/srv/apps/` and run
by the platform. See [hosting-an-app.md](hosting-an-app.md).

## Today

```mermaid
flowchart LR
    subgraph home["Home network"]
        subgraph pi["chocochip (Raspberry Pi)"]
            cron["cron"]
            run["/srv/apps/scheduler-tdc/run.sh"]
            bot["scheduler-tdc container<br/>Docker + Playwright"]
            metrics["metrics.py"]
            db[("metrics.db<br/>SQLite")]
        end
    end
    tutor["tutor.com"]
    subgraph aws["AWS us-east-1"]
        s3[("S3 bucket<br/>logs + screenshots")]
    end

    cron -->|"Wed 9:01"| run --> bot
    bot -->|"HTTPS"| tutor
    run -->|"aws s3 cp / sync<br/>IAM user scheduler-tdc-uploader"| s3
    cron -->|"every 5 min"| metrics --> db
```

### Where data lives

| Data | Location | Kept |
|---|---|---|
| Scheduler logs and screenshots | `/srv/apps/scheduler-tdc/{logs,screenshots}`, copied to S3 | 30 days local, S3 indefinitely |
| Health metrics | `/srv/homelab/platform/monitoring/metrics.db` | Not backed up yet (roadmap) |
| Secrets | `.env` in each app folder, `~/.aws/credentials` | Never in git |

## Planned: hosting sites

```mermaid
flowchart LR
    visitor["Visitor"] --> dns["Route 53<br/>(my domain)"]
    dns --> edge["EC2 edge (AWS)<br/>public IP, HTTPS, reverse proxy"]
    edge -->|"encrypted tunnel<br/>opened from home"| proxy["Nginx on the Pi / NUC"]
    proxy --> site1["Personal site"]
    proxy --> site2["Second site"]
```

- The sites are served from home hardware. AWS is the public front door.
- No ports are opened on the home router, and the home IP stays hidden.
- Optional later: an S3 + CloudFront copy of each site as a fallback when home is down.
