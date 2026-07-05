# Test Suite

## Required Checks

- Creating a payment with a fresh key stores the result and calls the provider once.
- Repeating the same key and payload returns the stored result and skips the provider.
- Repeating the same key with a changed amount returns conflict.
- Two concurrent calls with the same key cannot both call the provider.
- A provider timeout leaves a recoverable state and a later retry resolves it safely.

## Fixtures

- Customer with a valid payment source.
- Provider adapter that counts charge attempts and can force timeout.
- Repository fixture with transaction support and unique key enforcement.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing successful payment create response remains backward compatible.
- Declined payments do not get retried as successful charges.
- Audit metadata persists provider request id and response id when present.