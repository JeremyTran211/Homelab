# Runbook: set up the Pi from the Homelab and Scheduler_TDC repos

The Pi currently runs everything from `~/Project/Scheduler_TDC`. This sets up the new layout
next to it, tests it by hand, and only then points cron at it. The old folder isn't touched,
so rolling back is one command.

```
~/Project/Scheduler_TDC      ← live until step 6, don't touch
/srv/homelab                 ← Homelab repo (infra)
/srv/apps/scheduler-tdc      ← Scheduler_TDC repo (app)
```

**Timing:** switch cron (step 6) on any day except Wednesday morning. The new crontab runs the
scheduler every Wednesday at 9:01am. Until you switch, the old crontab keeps its Wed/Thu/Fri rotation:
Wed Oct 14, Thu Oct 22, Fri Oct 30, ...

## 1. Folders and clones

```bash
sudo mkdir -p /srv/apps
sudo chown jeremytran: /srv /srv/apps
```

Before the PRs are merged, clone the review branches. After they're merged, drop the `-b ...` part to get `main`.

```bash
git clone -b claude/blissful-hopper-5volvh https://github.com/JeremyTran211/Homelab.git /srv/homelab
git clone -b claude/blissful-hopper-5volvh https://github.com/JeremyTran211/Scheduler_TDC.git /srv/apps/scheduler-tdc
```

If a branch changes during review, run `git pull` in that folder.

## 2. Scheduler: secrets, image, safe checks

```bash
cd /srv/apps/scheduler-tdc
cp ~/Project/Scheduler_TDC/.env .env
grep S3_BUCKET= ~/Project/Scheduler_TDC/run_bot_rotating.sh   # copy the bucket value
nano .env    # add: S3_BUCKET=s3://<that bucket>   (see .env.example)
chmod 600 .env
docker compose build
```

None of these checks book anything:

```bash
# The image must not contain your password
docker run --rm --entrypoint ls scheduler-tdc:latest -a /app
# ✅ only main.py and requirements.txt

# The bot fails cleanly on bad config
docker compose run --rm -e TUTOR_EMAIL= scheduler; echo "exit=$?"
# ✅ "Missing TUTOR_EMAIL or TUTOR_PASSWORD" and exit=1
docker compose run --rm -e SCHEDULE=sundy scheduler; echo "exit=$?"
# ✅ "Unknown SCHEDULE 'sundy'" and exit=1

# run.sh finds its folder and .env
DRY_RUN=1 ./run.sh; echo "exit=$?"
tail -3 logs/cron-$(date +%F).log
# ✅ "DRY_RUN=1 ..." and "S3_BUCKET set: yes", exit=0

# S3 access
B=$(grep '^S3_BUCKET=' .env | cut -d= -f2-)
echo test > /tmp/t.txt && aws s3 cp /tmp/t.txt "$B/test/t.txt" && aws s3 rm "$B/test/t.txt"
# ✅ "upload: ..." then "delete: ..."
```

**Optional: one real run.** Plain `./run.sh` or `docker compose run --rm scheduler` **really logs in
and books** next week's hours (the same ones Wednesday's run would book). If booking hasn't opened yet,
expect the greyed-out button, then the check, then `exit=2` with screenshots in `screenshots/<date>/`.

## 3. Monitoring: venv and existing data

```bash
cd /srv/homelab/platform/monitoring
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ~/Project/Scheduler_TDC/health/metrics.db .     # test copy; copied again in step 6
.venv/bin/python metrics.py && .venv/bin/python health_check.py
# ✅ a new reading with the Pi's temperature, and "Status: OK"
```

## 4. Merge the PRs

Once everything above passes, merge both PRs on GitHub.

## 5. Switch both clones to `main`

```bash
cd /srv/homelab && git checkout main && git pull
cd /srv/apps/scheduler-tdc && git checkout main && git pull && docker compose build
```

## 6. Switch cron

```bash
cp ~/Project/Scheduler_TDC/health/metrics.db /srv/homelab/platform/monitoring/   # latest readings
crontab -l > ~/crontab.backup          # rollback copy
crontab /srv/homelab/hosts/pi/crontab
crontab -l                             # confirm
```

## 7. After the first Wednesday

This is the first real test of the new `main.py` against tutor.com.

- `tail -30 /srv/apps/scheduler-tdc/logs/cron-<date>.log` should show `Verified scheduled: [...]` and `Bot exit code: 0`
- Look through `/srv/apps/scheduler-tdc/screenshots/<date>/` to make sure they show the right page
- `aws s3 ls s3://<bucket>/<date>/ --recursive` should show the log and `screenshots/`
- `sqlite3 /srv/homelab/platform/monitoring/metrics.db "select count(*) from readings"` should be climbing

If the exit code is `2`, open `verification_mismatch.png` and check whether the hours were actually
unavailable or the check misread the page.

Once a couple of Wednesdays look good, retire the old folder:

```bash
mv ~/Project/Scheduler_TDC ~/Project/Scheduler_TDC.old
```

## Rollback

```bash
crontab ~/crontab.backup
```
