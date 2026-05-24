# Test Suite

## Required Checks

- Reported endpoint returns the expected missing-profile response instead of crashing.
- Any sibling matched path has either a regression test or an explicit out-of-scope rationale.
- Same-pattern scan evidence exists before final acceptance.
- Validation output is included in the closure package.

## Fixtures

- User with no profile record.
- User with a complete profile record.
- Optional sibling fixture for notification or serializer path.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- A one-line local null check without search evidence should fail review.
- A broad catch-all that turns all profile errors into empty names should fail review.
- A matched serializer crash left unfixed without rationale should fail review.