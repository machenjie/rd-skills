# Test Suite

## Required Checks

- Public tests for card and bank transfer success, decline, retryable failure,
  and provider-specific errors.
- Contract tests for any accepted strategy/interface/hierarchy.
- Review evidence rejects inheritance when taxonomy is absent.

## Fixtures

Payment fixtures include card payments, bank transfer payments, retryable
provider errors, terminal declines, and initialization configuration differences.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing card processing behavior stays unchanged.
- Existing bank transfer behavior stays unchanged.
- Callers do not branch on concrete subtype.
- Shared retry/formatting logic remains technical and private unless it has a
  current public contract.
