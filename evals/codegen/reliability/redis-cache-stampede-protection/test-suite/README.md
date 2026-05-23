# Test Suite

## Required Checks

- Hot key refresh is single-flight or lock-protected under concurrent cache misses.
- TTL jitter is applied instead of fixed synchronized expiration.
- Cache-down and lock-timeout behavior degrades safely.
- Metrics expose miss storm, hot key, lock contention, and fallback signals.

## Fixtures

- Fixture data for hot key refresh and cache miss storms.
- Fixture data for Redis unavailable behavior.
- Fixture data for tenant and permission scoped cache keys.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: TTL-only mutable cache with no invalidation.
- Reject shortcut: Tenant or permission data missing from cache key.
- Reject shortcut: No metric for miss storm or hot key.
- Existing successful behavior remains available after the new guard or compatibility path is added.
