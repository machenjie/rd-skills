# Test Suite

## Required Checks

- Permanent stale feature flag, fallback, compatibility branch, or deprecated API without deletion path is rejected.
- Caller search covers static, runtime, generated, reflection, package, and documentation references.
- Telemetry evidence or explicit accepted risk exists before removal.
- Rollback path and cleanup issue tracking are present.

## Fixtures

Cleanup fixtures belong to the profile migration boundary and must name target artifact, owner, removal condition, telemetry source, and rollback behavior.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Removed flag is absent from config, docs, and code.
- Generated client references are searched before compatibility shim deletion.
- Deprecated endpoint returns planned status during deprecation and is removed only after condition.
- Rollback can restore compatibility behavior if deletion causes consumer failure.
