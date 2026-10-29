---
name: commerce-fulfillment-extension
description: "For analysis/task/review agents: use for finite-resource reservation, order fulfillment, or returns; skip payment-only and simple catalog display."
---

# commerce-fulfillment-extension

## Role

Apply resource conservation and order-fulfillment state constraints without replacing financial or product-policy authority.

## When To Use

- Inventory, seats, time slots, or quotas move through reservation, confirmation, fulfillment, cancellation, or return.
- Expiry, late payment, partial fulfillment, or multiple locations affect resource availability.

## Do Not Use

- Only catalog labels, prices for display, or payment transport change.
- The workflow has no finite-resource or fulfillment state decision.

## Required Inputs

- Resource units and authority, reservation identity, order lines, effective prices, and channel/location scope.
- Expiry, payment, fulfillment, cancellation, and return policies with their concurrency and reconciliation boundaries.

## Professional Decision Rules

- Express conservation across available, reserved, fulfilled, returned, and retired resources using the product model.
- Identify the transition that owns each allocation and release.
- Make replayed cancellation or return incapable of releasing the same resource twice.
- Resolve reservation expiry and late payment through explicit product policy.
- Snapshot accepted price and promotion terms at the contractual point.
- Keep payment, order, and fulfillment states distinct across partial outcomes.
- Determine resale eligibility from the returned resource condition and location.

## High-Value Gotchas

- Payment completion does not prove fulfillment completion or restore an expired reservation.
- A quantity returned to accounting may remain unavailable for resale.

## Execution Checklist

1. Trace the resource ledger or equivalent authority through competing transitions.
2. Exercise duplicate cancellation, expiry/payment races, and partial returns.
3. Reconcile quantities and financial references across affected channels or locations.

## Stop / Escalation Conditions

- Stop when allocation authority, conservation rules, expiry policy, or return eligibility is undefined.
- Escalate an unresolved oversell, double-release, or irreversible fulfillment conflict.

## Output Contract

- Return resource/state relationships, transition authority, race resolution, conservation evidence, and unresolved commercial policy.

## Targeted References

- No task-local Reference is indexed for this Skill.
