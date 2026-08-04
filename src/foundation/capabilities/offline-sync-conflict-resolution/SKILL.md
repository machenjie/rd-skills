---
name: offline-sync-conflict-resolution
description: "`analysis-agent`/`task-agent`/`review-agent`: use for offline authority, pending operations, conflicts, cursors, transfers, or reconnect recovery; skip online-only work."
---

# offline-sync-conflict-resolution

## Registry Trigger

**Use when**

- An installed or browser client must read, write, queue, reconcile, delete, or resume work across loss and restoration of connectivity.

**Do not use when**

- The client is online-only, no synchronization behavior changes, or the open decision is a backend-wide transaction or distributed-consistency policy.

## Skill Role

Define client-side authority, pending-operation durability, optimistic reconciliation, revision and tombstone handling, partial synchronization, cursor recovery, unknown results, resumable transfers, and user recovery. Consume generic idempotency and transaction contracts without becoming their owner.

## High-Value Rules

- **Choose authority per data and operation.** Declare local-first, server-authoritative, or explicitly merged behavior before selecting queues or caches.
- **Persist pending intent with reconciliation identity.** Record the business operation, target identity, base revision, payload version, and user-visible status needed after restart.
- **Resolve unknown results before replay.** Query authoritative status or use proven duplicate suppression whenever a timeout or disconnect can hide a committed effect.
- **Separate optimistic presentation from confirmed truth.** Represent pending, accepted, rejected, conflicted, and abandoned outcomes so rollback cannot erase unrelated changes.
- **Use semantic revisions instead of client wall clocks.** Detect conflicts from authoritative versions or domain intent unless the contract explicitly tolerates clock skew and last-writer behavior.
- **Advance cursors only with applied state.** Commit page results, deletion markers, and checkpoint progress together so partial synchronization cannot skip or resurrect records.
- **Bind resumable transfer state to one upload.** Verify resource identity, processed offset, representation length, response completeness, current limits, expiry, and cancellation before appending bytes.
- **End blocked work in an owned recovery state.** Expose retry, discard, replace, merge, or support escalation according to consequence and user authority.

## Anti-Patterns

- Replay every queued request after reconnect without operation identity or authoritative status.
- Drop tombstones before every replica and offline client has crossed the deletion horizon.
- Resolve conflicts by device time while clock skew, account changes, or field-level intent remains material.

## Stop Conditions

Stop when authority, business operation identity, conflict policy, deletion horizon, or unknown-result resolution is absent. Escalate shared backend invariants to transaction, concurrency, or distributed-system owners.

## Output Contract

- offline-sync decision with authority pending-operation record retry unknown-result behavior optimistic states revision deletion policy partial-sync checkpoint transfer recovery user resolution evidence and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [sync reconciliation contracts](references/sync-reconciliation-contracts.md) | targeted | Authority conflict conditional write partial sync or resumable transfer choices compete | Current client and server contracts already establish one complete reconnect path | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, residual-risk |
