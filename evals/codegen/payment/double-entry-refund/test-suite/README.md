# Test Suite

## Required Checks

- Every refund creates balanced debit and credit ledger entries.
- Repeated provider refund events are idempotent.
- Partial refunds cannot exceed the refundable balance.
- Reconciliation surfaces provider mismatch without corrupting ledger state.

## Fixtures

- Fixture data for double entry ledger.
- Fixture data for refund idempotency.
- Fixture data for reconciliation.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Updating payment status without balanced ledger entries.
- Reject shortcut: Using floating point arithmetic for refund amounts.
- Existing successful behavior remains available after the new guard or compatibility path is added.
