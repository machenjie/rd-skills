# Test Suite

## Required Checks

- Direct API, SDK, schema, event, or public export field rename without compatibility path is rejected.
- Unknown consumer risk is named and mitigated.
- Generated-client migration guide and deprecation policy are required.
- Telemetry proves old and new usage before old behavior removal.

## Fixtures

Contract fixtures belong to the users API boundary and must include old field, new field, generated client, event payload version, and consumer type.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing mobile or backend consumer can still read `userName` during deprecation.
- New consumer can read `displayName`.
- Event payload compatibility is versioned.
- Rollback restores old contract behavior.
