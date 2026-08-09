# Test Suite

## Required Checks

- Reported endpoint returns the expected missing-profile response instead of crashing.
- Every match has a closed Finding Relation and action; authorized current-task
  matches have regression proof, while adjacent matches have rationale and
  residual risk and remain unedited.
- Same-pattern scan evidence exists before final acceptance.
- Validation results are included in the final handoff.

## Fixtures

- User with no profile record.
- User with a complete profile record.
- Optional sibling fixture for notification or serializer path.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- A one-line local null check without search evidence should fail review.
- A broad catch-all that turns all profile errors into empty names should fail review.
- Repairing an adjacent strict serializer, or leaving it without rationale and
  residual risk, should fail review.
