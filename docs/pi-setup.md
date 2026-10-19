# Pi setup

How to set up chocochip (Raspberry Pi) from these repos, either fresh or moving from the old
`~/Project/Scheduler_TDC` folder.

```
/srv/homelab               ← this repo
/srv/apps/scheduler-tdc    ← Scheduler_TDC repo (yours only: it holds the app's .env)
~/.aws/credentials         ← IAM user scheduler-tdc-uploader (never in git)
```

## 0. Fresh Pi only

Raspberry Pi OS 64-bit Lite, hostname `chocochip`, SSH enabled. Then:

```bash
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker jeremytran
# install the AWS CLI, then:
aws configure                        # region us-east-1
```

## 1. Folders and clones

```bash
sudo mkdir -p /srv/apps && sudo chown jeremytran: /srv /srv/apps
git clone https://github.com/JeremyTran211/Homelab.git /srv/homelab
git clone https://github.com/JeremyTran211/Scheduler_TDC.git /srv/apps/scheduler-tdc
```

## 2. Scheduler

```bash
cd /srv/apps/scheduler-tdc
cp .env.example .env && nano .env    # or copy from ~/Project/Scheduler_TDC/.env and add S3_BUCKET
chmod 600 .env
docker compose build
```

Safe checks (none of these book hours):

```bash
docker run --rm --entrypoint ls scheduler-tdc:latest -a /app       # ✅ no .env listed
docker compose run --rm -e TUTOR_EMAIL= scheduler; echo "exit=$?"  # ✅ exit=1
DRY_RUN=1 ./run.sh && tail -2 logs/cron-$(date +%F).log           # ✅ "S3_BUCKET set: yes"
aws sts get-caller-identity                                        # ✅ user/scheduler-tdc-uploader
```

## 3. Monitoring

```bash
cd /srv/homelab/platform/monitoring
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp ~/Project/Scheduler_TDC/health/metrics.db .     # only when moving from the old folder
.venv/bin/python metrics.py && .venv/bin/python health_check.py   # ✅ "Status: OK"
```

## 4. Cron

Do this any day except Wednesday morning.

```bash
crontab -l > ~/crontab.backup             # rollback: crontab ~/crontab.backup
crontab /srv/homelab/hosts/pi/crontab
crontab -l
```

## 5. After the first Wednesday

```bash
tail -30 /srv/apps/scheduler-tdc/logs/cron-<date>.log   # ✅ "Verified scheduled" and "Bot exit code: 0"
aws s3 ls s3://<bucket>/<date>/ --recursive             # ✅ log + screenshots
```

Exit code `2` means some hours weren't booked: check `screenshots/<date>/verification_mismatch.png`.
Once a couple of Wednesdays look good: `mv ~/Project/Scheduler_TDC ~/Project/Scheduler_TDC.old`.

## Troubleshooting

- **`InvalidClientTokenId` from aws:** the key itself was rejected. Re-run `aws configure`, or create a new key for the IAM user.
- **`aws s3 ls` gives AccessDenied:** expected. The IAM user can only see its own bucket (`aws s3 ls s3://<bucket>/`).
