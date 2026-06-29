# Test Suite

## Required Checks

- Verify two default calls do not share accumulated state.
- Verify explicit list input keeps the documented behavior.
- Verify no class or helper module is added for the local fix.

## Fixtures

Use repeated calls with different request IDs and one explicit list fixture.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- First default call cannot affect second default call.
- Explicit caller list behavior must remain stable.
- Mutable default argument must fail review.
