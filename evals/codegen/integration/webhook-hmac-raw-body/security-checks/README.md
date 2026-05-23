# Security Checks

## Threat Surface

This benchmark touches raw body signature verification, partner webhook contract, secret rotation, safe failure handling. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that signature comparison uses constant time comparison.
- Verify that verification happens before parsing and before idempotency side effects.
- Verify that tests use raw byte fixtures from the partner contract.
- Verify that logs include event id and rejection reason without secrets.

## Rejection Cases

- Reject any solution that uses verifying HMAC over JSON reserialization instead of raw body bytes.
- Reject any solution that uses accepting unsigned callbacks when configuration is missing.
- Reject any solution that uses running business handlers before signature verification succeeds.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
