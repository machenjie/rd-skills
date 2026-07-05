# Security Checks

## Threat Surface

This benchmark touches double entry ledger, refund idempotency, reconciliation, money precision. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that money values use integer minor units or exact decimal types.
- Verify that ledger writes are transactional with refund state changes.
- Verify that tests cover duplicate webhook, partial refund, and over refund denial.
- Verify that audit records include provider identifiers without sensitive payment data.

## Rejection Cases

- Reject any solution that uses updating payment status without balanced ledger entries.
- Reject any solution that uses using floating point arithmetic for refund amounts.
- Reject any solution that uses allowing duplicate provider events to post multiple refunds.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
