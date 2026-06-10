# Test Suite

## Required Checks

- Typed config validation covers defaults, invalid values, secrets boundaries, and fail-fast or safe degradation behavior.
- Feature flag owner, expiry, cleanup path, rollout, rollback, and kill switch are verified.
- Mode and kind switch hidden strategy drift is rejected.
- Domain and security invariants cannot be bypassed by config.

## Fixtures

Config fixtures belong to the notification boundary and must name scope, default, owner, expiry, and expected validation outcome.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Stale feature flag without cleanup fails review.
- Invalid tenant-level config cannot silently use legacy behavior.
- Hot reload does not apply partial invalid config.
- Cleanup owner/date is documented for temporary switches.
