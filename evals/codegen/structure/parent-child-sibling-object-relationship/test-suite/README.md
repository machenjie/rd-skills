# Test Suite

## Required Checks

- Public behavior tests for cancellation, refund eligibility, shipping holds,
  and combined lifecycle outcomes.
- Structure evidence declares parent-child or sibling relationship type.
- Tests avoid importing private sibling internals.

## Fixtures

Order fixtures include cancellable orders, shipped orders, refund-eligible
orders, disputed orders, and partially shipped orders.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing cancellation behavior remains unchanged.
- Refund behavior remains independent from shipping internals.
- Shipping decisions do not call cancellation internals.
- Parent orchestration is not a pass-through wrapper.
