# Test Suite

## Required Checks

- Verify empty input behavior.
- Verify missing/default values.
- Verify filtered records stay filtered.
- Verify returned record shape is unchanged.

## Fixtures

Use empty, missing-field, filtered, and normal record fixtures.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Nested comprehension with hidden defaults must fail review.
- Returned record shape must remain stable.
- Behavior-preservation tests are required.
