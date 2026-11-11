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

Scheduled apps run through `monitoring/run_app.py`, which records each run for the dashboard.
It reports the exit code of the app's `run.sh`, which is the exit code of the **last command in that
script**. If `run.sh` uploads logs after running the container, it must save the container's exit
code and finish with `exit` on that code, or a crashed app will show as a success.

Test the wrapper with a throwaway database and fake commands, never a real app:

```bash
METRICS_DB=/tmp/run-test.db python3 /srv/homelab/monitoring/run_app.py test-app sh -c 'exit 7'; echo $?   # ✅ 7
```

## 4. Dashboard

Shows Pi health and each app's last run. It runs in Docker all the time and only reads `metrics.db`.

```bash
id -u                                     # ✅ 1000 (if not, change USER in dashboard/Dockerfile to match)
cd /srv/homelab/dashboard
docker compose up -d --build              # first build takes a few minutes
docker compose ps                         # ✅ dashboard is "Up"
curl -s localhost:8000/api/health         # ✅ {"status":"OK", ...} with a recent reading
curl -s localhost:8000/api/apps           # ✅ [] until the first app runs through run_app.py
```

Then open `http://chocochip.local:8000` from a device on the home network (or use the address from
`hostname -I`). Never add a router port forward for it: the dashboard has no login.

## 5. Alerts

Messages you on Discord when the Pi or one of its apps has a problem. Create the webhook first:
Discord → Server Settings → Integrations → Webhooks → New Webhook → Copy Webhook URL.

```bash
cd /srv/homelab
cp .env.example .env
nano .env                                 # paste the URL after DISCORD_WEBHOOK_URL=
chmod 600 .env                            # it's a password: anyone with it can post
cd monitoring
python3 alerts.py --dry-run               # ✅ lists what it would send, sends nothing
python3 alerts.py                         # ✅ "Nothing to report." when all is well
```

Confirm messages actually arrive by pointing it at an empty database, which looks to it
like metrics have never been recorded:

```bash
python3 -c "import sqlite3; sqlite3.connect('/tmp/alert-test.db').close()"
METRICS_DB=/tmp/alert-test.db python3 alerts.py    # ✅ a message appears in Discord
```

Each problem is reported once, repeated daily while it lasts, and followed by a short
note when it clears. Thresholds live in `health_check.py`; per-app rules are the `APPS`
block at the top of `alerts.py`, including which exit codes count as normal.

## Updating

```bash
cd /srv/homelab && git pull
crontab /srv/homelab/pi.crontab           # only if pi.crontab changed
cd /srv/homelab/dashboard && docker compose up -d --build   # only if the dashboard or health_check.py changed
```

## Troubleshooting

- **`InvalidClientTokenId` from aws:** the key itself was rejected. Re-run `aws configure`, or create a new access key for the IAM user in the console.
- **`AccessDenied` on `aws s3 ls`:** expected. Each IAM user can only see its own bucket (`aws s3 ls s3://<bucket>/`).
- **A cron job never runs:** check `crontab -l`, and that the path exists. cron has a short `PATH`, so `pi.crontab` sets one at the top.
- **The dashboard says "Out of date":** `metrics.py` stopped writing. Check `crontab -l` and `/srv/homelab/monitoring/metrics.log`.
- **The dashboard won't start or shows errors:** `cd /srv/homelab/dashboard && docker compose logs`. A permissions error usually means your `id -u` doesn't match `USER` in `dashboard/Dockerfile`.
