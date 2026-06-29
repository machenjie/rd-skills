# Security Checks

## Threat Surface

Hidden transaction errors can falsely report successful writes.

## Required Checks

- Reject swallowed write errors.
- Fail if rollback is skipped after failed save.

## Rejection Cases

- Reject shadowed `err` that can hide failures.
- Reject success response on failed write.

