# Test Suite

## Required Checks

Invoke the candidate on actual Python source. Compare independent API values, exceptions, and release events. Check alias identity, shadows, byte offsets, atomic refusal, idempotence, and residual imports.

## Fixtures

`fixtures/passing/subject.py` implements the narrow contract. The starter is incomplete. `fixtures/faulty/subject.py` widens only the symbol-owner match to an unrelated API.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Reject rewriting an unrelated `fetch` symbol and approving compilation alone. Positive candidate assertions run separately; starter smoke is not positive behavior evidence.
