# Owned Financial State, Accounting, and Balances

Use this Reference only for the named owned-state, accounting, and balance decision.

## Decision Rules

- Model owned payment and ledger transitions across authorization, capture, settlement, failure, cancellation, refund, dispute, reversal, expiry, adjustment, and reconciliation. The model names transition authority, stale-event behavior, and compensation limits.
- Derive balancing, correction, reversal, and append-versus-update behavior from accounting ownership and storage guarantees. The result preserves financial history without imposing ledger semantics on pure orchestration.
- Define applicable available, pending, reserved, held, settled, negative, disputed, margin, and collateral balances. Their transition events and authoritative sources govern delayed or corrected execution.
