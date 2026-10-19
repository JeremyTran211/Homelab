# Pi setup

How to set up chocochip (Raspberry Pi) with this repo.

```
/srv/homelab           ← this repo
/srv/apps/<app>        ← one folder per app repo (owner-only: it holds the app's .env)
~/.aws/credentials     ← AWS keys from `aws configure` (never in git)
```

## 0. Fresh Pi only

Raspberry Pi OS 64-bit Lite, hostname `chocochip`, SSH enabled. Then:

```bash
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker jeremytran
# install the AWS CLI, then:
aws configure                        # region us-east-1
```

## 1. Folders and clone

```bash
sudo mkdir -p /srv/apps && sudo chown jeremytran: /srv /srv/apps
git clone https://github.com/JeremyTran211/Homelab.git /srv/homelab
```

Apps: clone each app repo into `/srv/apps/<app>` and follow that repo's README.

## 2. Monitoring

```bash
cd /srv/homelab/monitoring
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python metrics.py && .venv/bin/python health_check.py   # ✅ a reading, then "Status: OK"
```

Moving from an older setup? Copy your existing `metrics.db` into `/srv/homelab/monitoring/` first to keep its history.

## 3. Cron

Installing `pi.crontab` **replaces** the Pi's whole crontab, so back up the current one first.
Every job in it should point at a path that exists under `/srv`.

```bash
crontab -l > ~/crontab.backup             # rollback: crontab ~/crontab.backup
crontab /srv/homelab/pi.crontab
crontab -l                                # confirm
```

## Updating

```bash
cd /srv/homelab && git pull
crontab /srv/homelab/pi.crontab           # only if pi.crontab changed
```

## Troubleshooting

- **`InvalidClientTokenId` from aws:** the key itself was rejected. Re-run `aws configure`, or create a new access key for the IAM user in the console.
- **`AccessDenied` on `aws s3 ls`:** expected. Each IAM user can only see its own bucket (`aws s3 ls s3://<bucket>/`).
- **A cron job never runs:** check `crontab -l`, and that the path exists. cron has a short `PATH`, so `pi.crontab` sets one at the top.
