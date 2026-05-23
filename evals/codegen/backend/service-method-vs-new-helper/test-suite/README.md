# Test Suite

## Required Checks

- Cancellation succeeds before the deadline.
- Cancellation fails exactly at or after the deadline according to the product rule.
- Existing authorization and transaction behavior still runs through OrderService.
- No order-specific validation is added to shared utils.

## Fixtures

- Fixed clock set to the minute before the cancellation deadline.
- Fixed clock set exactly at the cancellation deadline.
- Fixed clock set after the cancellation deadline.
- Authorized and unauthorized order principals.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Adding validateCancellationDeadline to shared utils should fail review.
- Testing only a private helper should fail because public cancellation behavior is unproved.
- Bypassing OrderService should fail because transaction and authorization behavior can regress.
