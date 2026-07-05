# Test Suite

## Required Checks

- Per-operation client construction is rejected.
- Response body leak and stream leak are rejected on success and error paths.
- No pool sizing is rejected.
- Hidden network IO behind repository or adapter is rejected unless the decision record declares it.

## Fixtures

- Fake HTTP response requiring close.
- Error response requiring close.
- Reusable client or pool fixture.
- Slow upstream fixture for timeout behavior.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Per-operation client construction must fail review.
- Response body leak must fail tests or review.
- No pool sizing must fail reliability review.
- Hidden network IO behind repository or adapter must fail structure review.
