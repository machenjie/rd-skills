# Test Suite

## Required Checks

- Public behavior tests for service cancellation remain unchanged before and
  after the helper merge.
- Policy behavior tests remain independent of service orchestration tests.
- Value object invariant tests remain at the value object boundary.
- Adapter/client boundary tests or fakes verify side-effect translation without
  merging the client into service code.
- Static review or structure evidence rejects reckless file merge and lost
  small-file boundary failures.

## Fixtures

Order fixtures live under the orders test boundary and describe cancellable,
expired, disputed, and invalid-window states. Adapter fakes represent the
external payment boundary. Fixtures must not assert private helper call order.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing cancellation outcomes remain identical after the helper merge.
- `CancellationWindow` still rejects invalid windows through its public
  constructor or factory.
- `CancellationPolicy` remains testable through its public behavior contract.
- The service still depends on the adapter boundary rather than concrete
  external protocol details.
- Review fails any implementation that merges boundary files only to reduce file
  count.
