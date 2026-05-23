# Security Checks

## Threat Surface

This benchmark touches schema evolution, registry compatibility, consumer safety, replay readiness. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that schema checks run in CI and local benchmark scripts.
- Verify that tests include removed field, renamed field, and additive nullable field cases.
- Verify that compatibility policy is explicit per topic.
- Verify that metrics expose schema validation failures.

## Rejection Cases

- Reject any solution that uses publishing renamed or removed fields without compatibility checks.
- Reject any solution that uses testing only the latest consumer against the latest producer.
- Reject any solution that uses bypassing the registry in local tests.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
