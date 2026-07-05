# Test Suite

## Required Checks

- Verify failed save returns error.
- Verify rollback path is preserved.
- Verify shadowing is not left as a harmless-looking local.

## Fixtures

Use a repository fake that fails on save and records rollback.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Failed save must not return success.
- Rollback must happen on save failure.
- Shadowed error must fail review.
