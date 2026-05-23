# Test Suite

## Required Checks

- Changed shared packages select downstream test suites.
- Lockfile and generated contract changes invalidate affected test caches.
- Unknown paths fall back to a broader safe test set.
- CI output explains selected and skipped tests.

## Fixtures

- Fixture data for affected test selection.
- Fixture data for module graph accuracy.
- Fixture data for build cache safety.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Selecting tests only from direct file path prefixes.
- Reject shortcut: Ignoring lockfile or generated contract changes in cache keys.
- Existing successful behavior remains available after the new guard or compatibility path is added.
