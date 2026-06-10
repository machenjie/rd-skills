# Test Suite

## Required Checks

- Contract tests cover success, decline, retryable provider error, and terminal provider error.
- Callers do not branch on concrete provider classes.
- Provider creates client per request is rejected by static review.
- Base class only for shared code is rejected.

## Fixtures

- CardPay success and timeout responses.
- BankPay decline and retryable transport error responses.
- Reusable client or pool fixture with explicit shutdown.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- If/else scattered across service code must fail review.
- Provider creates client per request must fail review.
- No contract tests must fail the benchmark.
- Retry mapping must not be swallowed by a generic base class.
