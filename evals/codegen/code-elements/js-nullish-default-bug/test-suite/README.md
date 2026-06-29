# Test Suite

## Required Checks

- Verify missing values receive the fallback.
- Verify zero, false, and empty string remain unchanged.
- Verify no shared utility is introduced for the local expression.

## Fixtures

Use preference records with missing, zero, false, empty string, and normal values.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- A numeric zero preference must not become the fallback.
- A false boolean preference must not become the fallback.
- A missing preference must still use the fallback.
