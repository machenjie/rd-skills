# Test Suite

## Required Checks

- Update success is recorded only after boot health confirmation.
- Failed boot or missing heartbeat rolls back to the previous slot.
- Staged rollout pauses when health thresholds fail.
- Package identity and signature checks run before activation.

## Fixtures

- Fixture data for ota update lifecycle.
- Fixture data for a/b rollback.
- Fixture data for device health confirmation.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Marking OTA success before post boot health confirmation.
- Reject shortcut: Activating unsigned or identity mismatched packages.
- Existing successful behavior remains available after the new guard or compatibility path is added.
