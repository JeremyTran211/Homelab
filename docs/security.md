# Security

Both this repo and the app repos are public, so they're written assuming anyone can read them.

## Secrets

| Secret | Where it lives | Never in |
|---|---|---|
| App credentials (e.g. Tutor.com login) | `/srv/apps/<app>/.env` on the host | git, Docker images |
| S3 bucket names, AWS account ID | the app's `.env` | git |
| AWS access keys | `~/.aws/credentials` on the host (`aws configure`) | git, `.env`, Docker images |

How that's enforced:
- `.gitignore` in each repo ignores `.env`, keys, logs, screenshots and databases.
- Each app's `.dockerignore` keeps `.env` out of its image. Credentials reach the container at runtime through `env_file`.
- IAM policies in `cloud/aws/iam/` use `YOUR_BUCKET_NAME` placeholders.

## AWS access

The Pi uploads Scheduler_TDC's logs to S3 as a dedicated IAM user, `scheduler-tdc-uploader`.
It is not the root account and not an admin user.

| Control | Setting |
|---|---|
| Policy | Only `PutObject`, `ListBucket` and `DeleteObject`, only on the scheduler's log bucket ([template](../cloud/aws/iam/scheduler-s3-upload-policy.json)) |
| Permissions boundary | Set on the user, as a cap on top of the policy |
| Everything else | Denied. `aws s3 ls` (list all buckets) fails with `AccessDenied`, which is expected. |

`DeleteObject` is allowed on purpose, so test files can be cleaned up from the Pi. The trade-off:
a stolen key could delete logs in this one bucket, but nothing else.

**Checking it on the Pi**
```bash
aws sts get-caller-identity          # should show user/scheduler-tdc-uploader
aws s3 ls s3://<bucket>/             # works
aws s3 ls                            # AccessDenied (expected)
```

**If uploads stop:** `InvalidClientTokenId` means the key itself was rejected, not a permissions
problem. In Oct 2026 this happened between the Oct 1 and Oct 9 runs and was fixed by re-running
`aws configure` (root cause unknown). Check the user's access keys in the IAM console, and create a new
key if needed.

**Later:** replace long-lived keys with temporary credentials, using IAM Roles Anywhere or an SSM
hybrid activation (roadmap phase 2).

## People

Each collaborator gets their **own** GitHub account, Linux user on the Pi, and IAM user in AWS.
Logins are never shared, so access can be removed per person and actions are traceable.
The details are still to be decided (roadmap phase 0).

## Remote access

Nothing on the home network is exposed to the internet. When sites go public (roadmap phase 5),
traffic comes in through AWS and an encrypted tunnel opened from home, not through port forwarding.
