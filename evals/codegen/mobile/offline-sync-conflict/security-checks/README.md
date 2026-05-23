# Security Checks

## Threat Surface

This benchmark touches offline state, conflict resolution, versioned sync, user recovery. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that sync payloads include version or ETag preconditions.
- Verify that state management keeps pending, synced, failed, and conflict states distinct.
- Verify that tests simulate offline, reconnect, conflict, and retry flows.
- Verify that user visible errors do not discard unsynced edits.

## Rejection Cases

- Reject any solution that uses last write wins overwrite of server changes without conflict detection.
- Reject any solution that uses clearing offline drafts after a failed sync attempt.
- Reject any solution that uses retrying mutations without idempotency or version preconditions.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
