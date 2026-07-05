# Security Checks

## Threat Surface

This benchmark touches expand contract migration, rollback compatibility, deployment ordering, data integrity. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that migration scripts are idempotent and safe to resume.
- Verify that compatibility tests cover mixed old and new writer behavior.
- Verify that cleanup is gated behind explicit post rollout evidence.
- Verify that rollback plan avoids restore from backup for ordinary failure.

## Rejection Cases

- Reject any solution that uses dropping the legacy field in the first migration release.
- Reject any solution that uses backfilling with an irreversible transform and no audit trail.
- Reject any solution that uses rollback instructions that require restoring production backup.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
