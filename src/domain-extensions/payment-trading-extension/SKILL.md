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

- **Use authoritative provider evidence**: client redirects are not proof of authorization, capture, settlement, or revocation state. Bind authenticated server evidence to the intended transaction and account.
- **Control repeated financial effects**: choose provider or storage enforcement that prevents duplicate effects across retry, replay, and concurrent submission.
- **Match controls to custody**: approved raw-card custody carries current PCI evidence. Other flows keep sensitive values out of application storage and logs.
- **Enforce owned transitions**: define authority, retry, compensation, and correction for each owned state. Stale or impossible transitions receive rejection with auditable reasons.
- **Preserve ledger history**: corrections to an owned balance or audit ledger retain prior entries and traceability. Provider orchestration must not invent an ownerless ledger.
- **Use double entry only with accounting ownership**: a book of record proves balanced debits and credits. External status tracking instead reconciles provider balances.
- **Authenticate inbound events**: verify the provider's signature, freshness, identity, secret rotation, replay, and ordering contract.
- **Keep monetary arithmetic exact**: bind amount to currency, scale, rounding, conversion, overflow, and allocation semantics.
- **Bind regulation to accountable interpretation**: identify affected product, jurisdictions, actors, flows, assets, custody, and locations. The accountable legal or compliance owner maps applicable obligations to controls, evidence, exceptions, and release consequences; this Skill prescribes no universal regulatory rule.

## High-Value Gotchas

- a timeout hides a successful charge before retry
- fulfillment follows a client redirect instead of authoritative state
- out-of-order refund, dispute, or settlement events regress state
- an internal ledger has no accounting or reconciliation owner
- rounding differences create persistent settlement gaps

## Execution Checklist

1. Classify the system as provider orchestration, custody, ledger/book of record, trading, or a combination.
2. Trace authority, business identity, transitions, balances, and reconciliation ownership.
3. Prove duplicate, stale-event, reversal, rounding, authorization, and residual-risk behavior.

## Stop / Escalation Conditions

- Stop when source of truth, custody/accounting role, reconciliation owner, or regulatory scope is unknown.
- Escalate possible double charge, asset loss, ledger imbalance, unauthorized movement, or unreviewed regulated-data handling.

## Output Contract

- financial decision with invariant, authority, selected control, reconciliation limits, regulatory scope and accountable owner, control evidence, exceptions, release consequences, proof limits, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | money movement ledger order execution settlement or reconciliation behavior needs domain risk closure | the task only displays prices or ordinary orders without funds or execution state | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
