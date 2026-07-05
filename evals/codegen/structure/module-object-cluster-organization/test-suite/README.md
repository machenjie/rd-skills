# Test Suite

## Required Checks

- Public facade tests for allowed, denied, refund-hold, and adapter failure
  cancellation paths.
- Contract tests for any declared public DTO, repository, adapter, or policy
  contract.
- Static review evidence for public/private visibility and internal dependency
  direction.

## Fixtures

Order fixtures include cancellable orders, denied actors, disputed payment
orders, expired orders, and payment adapter failure.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing cancellation API behavior remains stable.
- Internal policies, repositories, adapters, mappers, and helpers are not
  imported from outside the module.
- The next cancellation rule has an obvious module location.
- Shared/common does not contain order cancellation business logic.
