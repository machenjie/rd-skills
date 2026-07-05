# Test Suite

## Required Checks

- Cancellation succeeds when the order is eligible and the actor is authorized.
- Cancellation fails at and after the configured deadline boundary.
- Authorization denial still happens before mutation.
- Structure evidence rejects shared utility placement for order business rules.

## Fixtures

- A cancellable order before the deadline.
- An order exactly at the deadline and one after the deadline.
- A principal without permission to cancel the order.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Adding `canCancelOrder` to shared utils should be rejected by review.
- Creating a stateless `OrderProcessor` should fail the structure rubric.
- Tests that assert only private helper calls should be rejected.
