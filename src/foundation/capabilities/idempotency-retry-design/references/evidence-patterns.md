# Idempotency Retry Evidence Patterns

Load this reference when closing duplicate-safety, unknown-outcome, tenant-isolation, crash-recovery, or terminal-resolution claims. Do not use it as a mechanism catalog.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Operation identity is stable | Entry points, principal/tenant/subject binding, canonical request/version rule, collision/conflict behavior | Does not prove the effect is coordinated with the record |
| Concurrent duplicates produce one effect | Same-identity overlap result, ownership transition, uniqueness/coordination evidence, caller-visible pending/result behavior | Does not cover crashes or externally owned effects |
| Record and effect survive crashes | Forced failures around acceptance, effect, result, publication, and acknowledgement; recovery result after restart | Cannot infer provider commit state without provider evidence |
| Unknown outcomes reconcile safely | Timeout/cancellation/transport-loss result when commit status is not proven, authoritative lookup, replay decision, reused or recovered result | Lookup freshness and authority remain explicit |
| Late replay remains bounded | Replay-source inventory, retention derivation, expiry/tombstone behavior, recovery/backfill result | Future replay sources are not covered |
| Layered retries do not amplify failure | Per-layer attempt/deadline/concurrency map, forced downstream degradation, cancellation and recovery result | Production spike shapes remain unproved unless measured |
| Terminal work has an owner | Observable terminal state, owner authority, reconciliation/compensation/manual action, audit trail | Owner response time and external recovery success are not guaranteed |
| Isolation is preserved | Cross-principal/tenant reuse and result-observation denial, log/artifact redaction | Does not prove callers or storage paths outside the inspected scope |

Treat old tests, runbooks, dashboards, prior task claims, and provider documentation as selectors until current source, configuration, failure injection, and owner evidence match the final change. Record inspected and skipped retry layers, stores, effects, replay sources, and external authorities.

Block closure when mutation replay lacks stable identity, record and effect ordering is unknown, or same-identity concurrency can produce conflicting business effects. Also block unreconciled unknown outcomes, late replay beyond protection, unowned terminal work, and reachable cross-tenant result reuse.
