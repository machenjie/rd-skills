---
name: payment-trading-extension
description: "For analysis, task, or review agents using a Professional Skill on payments, trading, ledgers, settlement, refunds, or reconciliation; not for non-financial or Web3-only work."
---

# payment-trading-extension

## Role

Apply this focused Layer 3 Domain Skill to affected financial state. Give
`analysis-agent`, `task-agent`, and `review-agent` money-movement, custody,
ledger, settlement, reconciliation, and regulatory constraints for affected
financial state.

## When To Use

- payment, billing, refund, ledger, balance, settlement, trading, order, wallet, or money movement

## Do Not Use

- non-financial workflows or chain-only custody and transactions
- price display or ordinary orders without funds, ledger, settlement, or execution state

## Required Inputs

- monetary owner, representation, provider or custody role, and state machine
- source of truth, reconciliation owner, regulatory scope, recovery, and provider contract

## Professional Decision Rules

- Preserve the accepted financial invariant across authoritative state, duplicate effects, custody, owned transitions, ledger/accounting boundaries, inbound events, exact arithmetic, reconciliation, and accountable regulation.
- Load the named Reference for detailed closure.

## High-Value Gotchas

- A timeout, redirect, stale event, ownerless ledger, or rounding drift is not authoritative financial completion.

## Execution Checklist

1. Establish the financial invariant and authoritative state.
2. Load each named Reference whose decision problem is active.
3. Record selected controls, reconciliation evidence, proof limits, and residual risk.

## Stop / Escalation Conditions

- Stop when source of truth, custody/accounting role, reconciliation or regulatory owner, or a possible double-charge, asset-loss, imbalance, unauthorized-movement, or regulated-data consequence remains unresolved.

## Output Contract

- financial decision with invariant, authority, selected control, reconciliation limits, regulatory scope and accountable owner, control evidence, exceptions, release consequences, proof limits, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [financial role and state authority](references/financial-role-and-state-authority.md) | targeted | payment custody model, provider/custody/ledger/settlement roles, source of truth, or authoritative completion state is open | roles, source of truth, custody and authoritative state are already explicit, or no monetary state exists, including price display or ordinary orders without funds, ledger, settlement, or execution state | analysis-agent, task-agent, review-agent | boundary-decision, residual-risk |
| [raw card custody evidence](references/raw-card-custody-evidence.md) | evidence-pattern | approved raw-card custody requires PCI/PAN/CVV retention, storage, display, logging, or evidence closure | no raw-card custody exists; the flow is provider-hosted/non-custodial | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [non custodial sensitive data boundary](references/non-custodial-sensitive-data-boundary.md) | targeted | tokenized/provider-hosted payment flow must prove PAN/CVV/payment-secret exclusion | application has no reachable payment secret, or approved raw-card custody rather than a non-custodial boundary is being assessed | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, residual-risk |
| [duplicate financial effect control](references/duplicate-financial-effect-control.md) | targeted | retry, replay, concurrent submission, result reuse, or unknown outcome can repeat a financial effect | no retryable financial effect exists, or current provider/storage uniqueness is already proven and unchanged | analysis-agent, task-agent, review-agent | selected-approach, residual-risk |
| [owned financial state accounting and balances](references/owned-financial-state-accounting-and-balances.md) | targeted | owned payment/ledger transitions, correction history, accounting ownership, or balance authority is open | pure provider orchestration owns no ledger, accounting book, or application balance | analysis-agent, task-agent, review-agent | decision-record, residual-risk |
| [trading order execution and identity](references/trading-order-execution-and-identity.md) | targeted | order acknowledgement/fill/cancel/replace, execution identity, race, gap, or recovery behavior is open | payment-only work has no order execution, fill, cancel, venue identity, or trading-session recovery | analysis-agent, task-agent, review-agent | decision-record, failure-decision, residual-risk |
| [market data and trading risk controls](references/market-data-and-trading-risk-controls.md) | targeted | price-sensitive execution, risk limits, overrides, kill switch, leverage, margin, or liquidation behavior is open | no price-sensitive execution, leverage, override, limit, or kill-switch behavior changes | analysis-agent, task-agent, review-agent | selected-approach, failure-decision, residual-risk |
| [venue product monetary and calendar contracts](references/venue-product-monetary-and-calendar-contracts.md) | targeted | venue/product units, tick/lot/notional, fee/funding, precision/rounding, currency, cutoff, calendar, or timestamp contract is open | no venue/product monetary representation or calendar contract changes, and current contracts are explicit | analysis-agent, task-agent, review-agent | decision-record, residual-risk |
| [provider venue event authentication](references/provider-venue-event-authentication.md) | targeted | inbound provider/venue events require identity, replay, ordering, version, credential, or audit closure | no inbound external financial event is consumed | analysis-agent, task-agent, review-agent | boundary-decision, residual-risk |
| [financial reconciliation and monitoring](references/financial-reconciliation-and-monitoring.md) | targeted | orders, executions, positions, balances, ledgers, settlements, corrections, breaks, replay windows, or operational signals require reconciliation closure | no cross-source reconciliation or financial-operability boundary changes | analysis-agent, task-agent, review-agent | decision-record, validation-plan, residual-risk |
