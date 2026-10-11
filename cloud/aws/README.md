# AWS

One AWS account, region `us-east-1`. Everything here is set up by hand in the console for now.
Terraform comes later.

## What exists

| Resource | Used by | Purpose |
|---|---|---|
| S3 bucket (name in the app's `.env`) | Scheduler_TDC | Bot logs and screenshots, one folder per run date |
| IAM user `scheduler-tdc-uploader` | Scheduler_TDC on the Pi | Uploads to that bucket only. Has [`iam/scheduler-s3-upload-policy.json`](iam/scheduler-s3-upload-policy.json) plus a permissions boundary. |

See [docs/security.md](../../docs/security.md) for how to check the Pi's access.

## Rules

- One IAM user (or role) per app, scoped to only what that app needs.
- Bucket names and the account ID stay out of this repo. Policies here use `YOUR_BUCKET_NAME` as a placeholder.

## Planned

- Public edge for hosted sites: Route 53 (DNS) and a small EC2 instance in front of the homelab (see the roadmap)
- CloudWatch logs and metrics, SNS alerts
- S3 lifecycle rules and backups
