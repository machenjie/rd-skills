# Offline Synchronization And Reconciliation Contracts

Use only when authority, reconnect, conditional-write, incremental-sync, or resumable-transfer designs compete. Sources accessed 2026-07-24.

## Decision Matrix

| Decision | Contract |
|---|---|
| Read | Name authority/freshness per mode; reject incomparable local/network truth. |
| Write | Choose online-only, queued, or local-first by durability/consequence; preserve input. |
| Pending | Persist business/target identity, revision, payload version, owner, terminal states; distinguish replay. |
| Unknown | Reconcile authoritative status or proven duplicate suppression before repeat; timeout stays uncertain. |
| Optimistic | Separate confirmed base/overlay; change its operation and preserve unrelated changes. |
| Conflict | Use authoritative version, field semantics, mergeability, owned choice; reject device-time wins. |
| Incremental | Apply pages, tombstones, checkpoint atomically; define expiry/reset; prevent skip/resurrection. |
| Transfer | Bind upload identity, processed offset, length, completeness, current limits, expiry, cancellation; reject invalid appends. |

## Evidence And Proof Limits

Android defines offline strategy/conflict. HTTP idempotency/conditions omit business identity/merge policy. Google/Microsoft expose deletion, duplicates, cursor expiry, and checkpoints. IETF draft 12 defines upload identity, processed offset, completeness, and limits but can change. Provider contracts cannot prove repeat-safe effects, comparable clocks, or cursor-complete writes.

Sources: [Android](https://developer.android.com/topic/architecture/data-layer/offline-first), [HTTP](https://www.rfc-editor.org/rfc/rfc9110.html), [Google](https://developers.google.com/workspace/calendar/api/guides/sync), [Microsoft](https://learn.microsoft.com/en-us/graph/delta-query-overview), [IETF](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-resumable-upload-12).

## Required Record

Return authority, pending schema, retry/unknown result, optimism/conflict, cursor/deletion transaction, transfer identity, recovery, versions, and proof limits.

## Anti-Patterns

- Replay without identity or authoritative status.
- Drop tombstones before replica horizons.
- Resolve conflicts by device time.
