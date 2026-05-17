# Example Output

## Payment Trading Domain Findings
- Blocking: checkout may not grant subscription entitlement from the browser success redirect; entitlement starts after server-verified provider confirmation.
- Required state model: created, authorized, captured, settled, failed, canceled, refunded, disputed, reconciled.
- Ledger requirement: every provider event creates immutable balanced entries or a reconciliation exception.

## Verification
- Contract tests for webhook replay, duplicate client retry, provider timeout, refund, and dispute paths.
- Reconciliation test comparing provider report, internal ledger, invoice, and user-visible balance.
- Monitoring for unreconciled payments, duplicate idempotency keys, ledger imbalance, and failed entitlement activation.
