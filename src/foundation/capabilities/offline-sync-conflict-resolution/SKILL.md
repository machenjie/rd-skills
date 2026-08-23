---
name: offline-sync-conflict-resolution
description: "Use for offline reconciliation, conflicts, cursors, transfers, or reconnect recovery; skip online-only and backend-wide policy."
---

# offline-sync-conflict-resolution

## Registry Trigger

**Use when**

- An offline-reconciliation decision is active.

**Do not use when**

- Skip online-only clients and backend-wide transaction or distributed-consistency policy.

## Skill Role

Own client authority, durable intent, reconciliation, checkpoints, transfers, and recovery; exclude backend transaction and idempotency policy.

## High-Value Rules

- **Choose authority.** Define read/write authority and pending-operation identity.
- **Resolve uncertainty.** Reconcile unknown, optimistic, and conflicted outcomes.
- **Commit progress.** Require atomic page, tombstone, and checkpoint application.
- **Define recovery.** Bind transfers and user resolution to authoritative state.

## Anti-Patterns

- Local success is not offline-reconciliation contract proof.

## Stop Conditions

Stop on unknown authority, operation identity, conflict policy, deletion horizon, or result.

## Output Contract

- offline-sync decision with authority pending-operation record retry unknown-result behavior optimistic states revision deletion policy partial-sync checkpoint transfer recovery user resolution evidence and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [sync reconciliation contracts](references/sync-reconciliation-contracts.md) | targeted | Authority conflict conditional write partial sync or resumable transfer choices compete | Current client and server contracts already establish one complete reconnect path | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, residual-risk |
