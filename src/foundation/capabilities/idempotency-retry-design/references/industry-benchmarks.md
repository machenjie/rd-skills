# Idempotency And Retry Decision Patterns

Load this reference only when current operation semantics leave multiple identity, coordination, retry, or late-replay designs viable. Named mechanisms are candidates, not universal requirements.

| Decision | Evidence to compare | Reject when |
| --- | --- | --- |
| Identity scope | Business uniqueness, caller/tenant boundary, canonical request meaning, version evolution, collision domain | A transport attempt is mistaken for a business operation |
| Coordination boundary | Local transaction reach, external effect authority, publication/acknowledgement order, restart behavior | Check-then-act leaves a duplicate-or-loss window |
| In-flight ownership | Concurrency model, lease/fencing semantics where applicable, takeover rule, caller wait/poll contract | Concurrent or stale ownership can produce duplicate or conflicting business effects |
| Result model | Pending/succeeded/failed/unknown semantics, reusable response, redaction and authorization | A duplicate is reported complete without an established result |
| Unknown-outcome recovery | Authoritative lookup, safe replay proof, compensation/reconciliation authority | Timeout or cancellation decides whether the effect happened while commit status is unproved |
| Retention and expiry | Reachable replay horizons, storage/privacy cost, backfill and disaster-recovery behavior | Protection expires while a reachable replay remains valid |
| Retry budget | Combined layers, downstream capacity, provider pacing, cancellation, recovery shape | Independent retries multiply load or outlive the operation's value |
| Terminal resolution | Observable state, owner, recovery authority, accepted-loss rule, audit need | Exhaustion becomes silent loss or endless work |

Candidate coordination mechanisms include natural business uniqueness, conditional persistence, durable operation records, coordinated publication, receiver deduplication, and authoritative provider lookup. Select only mechanisms supported by the actual transaction and trust boundaries; no candidate by itself proves external-effect coordination.

Proof scope: these patterns do not establish transaction commit ordering, broker acknowledgement semantics, provider status authority, workflow recovery, or downstream capacity. Require fresh evidence from the owning boundary before claiming those properties.
