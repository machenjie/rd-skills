# Test Suite

## Required Checks

- Offline edits sync only when based on the expected server version.
- Conflicts preserve local draft data and expose a recovery path.
- Retry behavior handles network loss without duplicate mutation effects.
- Telemetry distinguishes success, retry, and conflict outcomes.

## Fixtures

- Fixture data for offline state.
- Fixture data for conflict resolution.
- Fixture data for versioned sync.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Last write wins overwrite of server changes without conflict detection.
- Reject shortcut: Clearing offline drafts after a failed sync attempt.
- Existing successful behavior remains available after the new guard or compatibility path is added.
