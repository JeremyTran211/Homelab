# CLAUDE.md

Infrastructure for a hybrid on-prem + AWS homelab, running on a Raspberry Pi (`chocochip`).
Apps live in their own repos (e.g. Scheduler_TDC). App code doesn't belong here.
Two people work on this and both are learning: explain changes in plain terms, and give exact
commands for anything that has to be done by hand on the Pi or in the AWS console.

The repo is public.

## Rules

- Never commit secrets or personal infra details: `.env`, AWS keys, bucket names, the AWS account ID.
  Use placeholders like `YOUR_BUCKET_NAME`.
- Work on a branch and open a PR. Never push to `main`.
- Small steps, each one explained. Changes get approved one at a time.
- Keep docs lean: update `README.md`, `ROADMAP.md` or `docs/pi-setup.md` rather than adding new doc files.
- `hosts/pi/crontab` is the source of truth for the Pi's cron. Editing it doesn't change the Pi;
  it's installed by hand with `crontab /srv/homelab/hosts/pi/crontab`.

## Careful

- Scheduler_TDC books real Tutor.com hours. Never run it for real to test; use `DRY_RUN=1 ./run.sh`.
- The Pi is ARM64: anything in Docker must work on `linux/arm64`.
- Nothing on the home network gets exposed directly to the internet.

## Testing

`python3 -m py_compile <file>`, `bash -n <script>`, `python3 -m json.tool <policy>.json`.
For anything that runs on the Pi, put the commands and expected output in the PR.
