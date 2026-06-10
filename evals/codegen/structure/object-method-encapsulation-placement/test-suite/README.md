# Test Suite

## Required Checks

- Public behavior tests for allowed, denied, expired, refund-hold, and payment
  failure cancellation paths.
- Structure evidence verifies method placement before class creation.
- Tests do not import private helpers.

## Fixtures

Order fixtures cover standard orders, premium grace orders, expired orders,
disputed payment orders, denied actors, and payment adapter failure.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing cancellation behavior stays unchanged.
- Adapter side effects remain observable at service/adapter boundaries.
- Domain/value objects do not import infrastructure concerns.
- Private helper behavior remains covered through public behavior.
