# chocochip (Raspberry Pi)

| | |
|---|---|
| Role | Runs every lab service today |
| Admin user | `jeremytran` (shared access for collaborators: to be decided) |
| Timezone | America/Los_Angeles |
| Installed | Docker + compose plugin, AWS CLI (region us-east-1), Python 3 |

## Folder layout

```
/srv/homelab               ← this repo (infra): crontab, monitoring, docs
/srv/apps/<app-name>       ← one clone per app repo, e.g. /srv/apps/scheduler-tdc
```

**Who owns what:** `/srv/homelab` is shared by everyone working on the infrastructure
(planned: a `homelab` group). Each app folder belongs to the app's owner only, because it
holds that app's `.env`. Infra collaborators don't need access to app folders.

One-time setup for these folders:

```bash
sudo mkdir -p /srv/apps
sudo chown jeremytran: /srv /srv/apps
```

## Scheduled jobs

[`crontab`](crontab) is the source of truth. Install it with `crontab /srv/homelab/hosts/pi/crontab`.

| When | Job | Repo |
|---|---|---|
| Wednesday 9:01am | `/srv/apps/scheduler-tdc/run.sh` | [Scheduler_TDC](https://github.com/JeremyTran211/Scheduler_TDC) |
| Every 5 min | `platform/monitoring/metrics.py` | this repo |

## Secrets on this host (not in git)

- `/srv/apps/scheduler-tdc/.env`
- `~/.aws/credentials` (IAM user `scheduler-tdc-uploader`)

## Rebuild from scratch

1. Flash Raspberry Pi OS (64-bit Lite), set the hostname to `chocochip`, enable SSH.
2. Install Docker (`curl -fsSL https://get.docker.com | sh`), then `sudo usermod -aG docker jeremytran`.
3. Install the AWS CLI and run `aws configure`.
4. Follow [the migration runbook](../../docs/runbooks/pi-migration.md), restoring `.env` files from your password manager.
