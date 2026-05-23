# Test Suite

## Required Checks

- Old and new application versions can run during the migration window.
- Forward migration, backfill, read cutover, and cleanup are separated.
- Rollback returns traffic to the previous version without data loss.
- Deployment notes include stop conditions and verification commands.

## Fixtures

- Fixture data for expand contract migration.
- Fixture data for rollback compatibility.
- Fixture data for deployment ordering.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Dropping the legacy field in the first migration release.
- Reject shortcut: Backfilling with an irreversible transform and no audit trail.
- Existing successful behavior remains available after the new guard or compatibility path is added.
