# Test Suite

## Required Checks

- Producer schema changes are checked for declared compatibility mode.
- Consumer fixtures prove old and new event versions can be read.
- Incompatible changes fail before publication.
- Replay documentation covers versioned deserialization and dead letter handling.

## Fixtures

- Fixture data for schema evolution.
- Fixture data for registry compatibility.
- Fixture data for consumer safety.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Publishing renamed or removed fields without compatibility checks.
- Reject shortcut: Testing only the latest consumer against the latest producer.
- Existing successful behavior remains available after the new guard or compatibility path is added.
