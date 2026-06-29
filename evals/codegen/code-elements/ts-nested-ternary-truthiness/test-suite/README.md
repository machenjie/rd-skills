# Test Suite

## Required Checks

- Verify empty label renders as valid.
- Verify zero count renders as valid.
- Verify missing value uses fallback.
- Verify disabled state remains correct.

## Fixtures

Use rendered component states with empty label, zero count, missing value, and disabled input.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Empty label must not become fallback.
- Zero count must not become fallback.
- Nested ternary truthiness must fail review.
