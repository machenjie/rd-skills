# Benchmark Prompt

## Task

Implement a focused change to implement refund posting with double entry ledger integrity and idempotent provider reconciliation.

## Context

The starter repo represents a billing service records charges and needs to post partial and full refunds. In its initial state, the starter behavior updates payment status without balanced ledger entries. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Every refund creates balanced debit and credit ledger entries.
- Repeated provider refund events are idempotent.
- Partial refunds cannot exceed the refundable balance.
- Reconciliation surfaces provider mismatch without corrupting ledger state.

## Constraints

- Money values use integer minor units or exact decimal types.
- Ledger writes are transactional with refund state changes.
- Tests cover duplicate webhook, partial refund, and over refund denial.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
