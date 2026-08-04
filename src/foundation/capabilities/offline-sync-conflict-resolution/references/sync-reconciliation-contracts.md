# Offline Synchronization And Reconciliation Contracts

Use this reference when client authority, reconnect behavior, conditional writes, incremental synchronization, or resumable transfer still has competing designs.

Official pages in this reference were recorded as accessed on 2026-07-24.

## Decision Matrix

| Decision | Required facts | Safe selection test | Failure signal |
|---|---|---|---|
| Read authority | Local usability need, server truth, freshness, and stale-data consequence | One named source feeds the visible state in each connectivity mode | UI alternates between incomparable local and network values |
| Write admission | Online requirement, local durability, consequence, and user expectation | Choose online-only, queued, or local-first per operation | Critical user input disappears on disconnect |
| Pending operation | Business identity, base revision, payload version, owner, and terminal states | Persist enough intent to reconcile after process restart | Queue entry cannot distinguish replay from a new action |
| Unknown result | Status lookup, duplicate suppression, and authoritative effect | Reconcile before repeat when commit might have occurred | Timeout is treated as definite failure |
| Optimistic state | Pending overlay, confirmed base, rejection, conflict, and dependent edits | Remove or transform only the affected overlay | Rollback erases later unrelated user changes |
| Conflict | Authority, version, field semantics, mergeability, and user choice | Preserve domain intent or surface an owned conflict | Device timestamp silently overwrites concurrent work |
| Incremental sync | Query scope, page token, final cursor, deletion markers, and reset path | Advance the durable cursor only after all pages apply | Crash skips a page or resurrects a deleted record |
| Resumable transfer | Upload identity, processed offset, representation length, response completeness, current limits, expiry, and cancellation | Query current resource state and reconcile completion before append | Bytes are duplicated, appended after completion, or attached to the wrong upload |

## Source-Derived Constraints

- Android's offline-first guidance treats read and write strategies as explicit data-layer choices and warns that local-first writes require conflict handling.
- HTTP defines method idempotency and conditional requests, but those semantics do not create a business operation identity or merge policy.
- Incremental APIs demonstrate that deletions, duplicate appearances, expired cursors, and multi-page checkpoints are normal protocol outcomes.
- The IETF resumable-upload work defines one resource per upload, a processed-data offset, and response completeness that can end resumption.
- The cited resumable-upload source remains an active Internet-Draft rather than a final RFC.

## Primary Sources

- [Android build an offline-first app](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [Google Calendar incremental synchronization](https://developers.google.com/workspace/calendar/api/guides/sync)
- [Microsoft Graph delta query overview](https://learn.microsoft.com/en-us/graph/delta-query-overview)
- [IETF resumable uploads for HTTP draft 12](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-resumable-upload-12)

## Version And Inference Limits

The Android and service-provider pages are rolling documentation and describe their own products. Google sync tokens and Microsoft delta links are examples, not interchangeable universal contracts.

RFC 9110 is stable HTTP semantics. `draft-ietf-httpbis-resumable-upload-12`, published 2026-07-06 and expiring 2027-01-07 when accessed, is work in progress and may change or be replaced.

The `-12` change log against `-11` changes offset, response-completeness, limit, cancellation, and retry guidance; the resumable-transfer decision above therefore uses processed offset, response completeness, and current limits. It does not change this Skill's offline authority, operation identity, conflict, tombstone, or cursor rules.

Do not infer that HTTP idempotency makes an application effect repeat-safe, that server time is comparable to device time, or that a cursor proves all local writes and deletions were applied.

## Required Record

Return the selected authority, pending-operation schema, retry and unknown-result contract, optimistic states, conflict inputs, cursor and deletion transaction, resumable-transfer identity, user recovery, protocol versions, and proof limits.
