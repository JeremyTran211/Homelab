# CLAUDE.md

Notes for Claude Code when working in this repo.

## What this is

The infrastructure for a hybrid on-prem + AWS homelab: the machines, shared services,
scheduling, monitoring and AWS setup that apps run on. It runs on a Raspberry Pi (`chocochip`)
today; an Intel NUC12 joins later.

Two people work on this, and both are learning. Explain changes in plain terms and walk us
through anything that has to be done by hand on a host or in the AWS console.

**This repo is infrastructure only.** Apps and sites live in their own repos (e.g.
[Scheduler_TDC](https://github.com/JeremyTran211/Scheduler_TDC)). App code doesn't belong here.
How an app gets hosted is in `docs/hosting-an-app.md`.

The repo is **public** and doubles as a portfolio project.

## Layout

| Path | What's there |
|---|---|
| `hosts/<host>/` | Per-machine config. `hosts/pi/crontab` is the source of truth for the Pi's cron. |
| `platform/` | Shared services. Today: `monitoring/` (Pi health metrics to SQLite every 5 min). |
| `cloud/aws/` | AWS notes and IAM policy templates |
| `docs/` | Architecture, hosting an app, roadmap, security, setup log, runbooks |

On the Pi, this repo is cloned to `/srv/homelab`, and each app repo to `/srv/apps/<app-name>`.

## Rules

- **Never commit secrets or personal infrastructure details.** That includes `.env` files, AWS keys,
  bucket names and the AWS account ID. Use placeholders like `YOUR_BUCKET_NAME`.
- **Work on a branch and never push to `main`.** Changes are reviewed and merged through PRs.
- **Make changes in small steps and explain each one.** Changes get approved one at a time.
- **Don't commit runtime data** (logs, `*.db`). The root `.gitignore` covers these.
- Editing `hosts/pi/crontab` doesn't change the Pi. It's installed there by hand with
  `crontab /srv/homelab/hosts/pi/crontab`.
- Anything done by hand on a host or in AWS gets a line in `docs/setup-log.md`, newest first.
- Update the docs (README, `docs/architecture.md`, the roadmap) when a change makes them wrong.
- One IAM user or role per app or person, scoped to what it needs. No shared logins.

## Careful

- Some apps act on the real world. For example, Scheduler_TDC books real Tutor.com hours.
  Never run an app's real job to test infrastructure; use the app's dry-run mode.
- The Pi is ARM64. Anything run in Docker must work on `linux/arm64`.
- Shell scripts must keep LF line endings (`.gitattributes` enforces this).
- Nothing on the home network gets exposed directly to the internet. Public traffic will come
  through AWS and a tunnel opened from home (see `docs/architecture.md`).

## Testing changes

- Python: `python3 -m py_compile <file>`, then run the script.
- Shell: `bash -n <script>`. Crontab lines: check the paths exist in the runbook's layout.
- JSON policies: `python3 -m json.tool <file>`.
- Anything that has to run on the Pi or in AWS: add the exact commands, with the expected output,
  to the PR or a runbook.
