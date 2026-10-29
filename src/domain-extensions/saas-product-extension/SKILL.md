---
name: saas-product-extension
description: "For analysis/task/review agents: use for subscription, entitlement, usage, or seat lifecycle; skip ordinary tenant queries and one-time payments."
---

# saas-product-extension

## Role

Apply SaaS lifecycle constraints to subscription, entitlement, and usage decisions within the existing Professional owner.

## When To Use

- Trial, renewal, grace, cancellation, plan changes, refunds, or seat limits affect product access.
- Usage corrections or asynchronous billing events can diverge from entitlement state.

## Do Not Use

- The task changes ordinary tenant lookup or one-time payment behavior without a subscription lifecycle.
- A provider name appears without a SaaS state or policy decision.

## Required Inputs

- Product policy, organization/workspace identity, subscription and entitlement authorities, and effective-time rules.
- Invoice/payment events, usage identity, seat/quota definitions, provider ordering, and retention policy.

## Professional Decision Rules

- Model organization, subscription, invoice, payment, entitlement, and usage as distinct facts with explicit relationships.
- Derive access from the product entitlement policy, not a single provider payment flag.
- Separate event occurrence, receipt, and policy effective times.
- Preserve pending plan changes until their contractual effective time.
- Reconcile duplicate, late, corrected, and reordered usage or billing events.
- Define how cancellation, restoration, refunds, and deletion affect rights and retained data.

## High-Value Gotchas

- A failed payment can coexist with valid grace-period access.
- A refund, canceled invoice, and canceled subscription need not imply the same entitlement transition.

## Execution Checklist

1. Trace the affected lifecycle through effective dates and authoritative facts.
2. Exercise duplicate, late, and competing transitions against the product policy.
3. Compare financial, subscription, and entitlement outcomes after reconciliation.

## Stop / Escalation Conditions

- Stop access changes when the governing policy, effective time, or authoritative subscription identity is unresolved.
- Escalate contradictions between restoration, deletion, retention, and previously granted rights.

## Output Contract

- Return state relationships, policy/effective-time decisions, reconciliation outcomes, temporal validation, and remaining policy ambiguity.

## Targeted References

- No task-local Reference is indexed for this Skill.
