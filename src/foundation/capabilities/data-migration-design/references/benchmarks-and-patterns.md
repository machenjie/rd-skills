# Data Migration Design Benchmarks And Patterns

Load this reference when migration type, mixed-version phases, backfill/cutover, rollback tier, or production proof changes the design. Storage-specific tools are candidates only after current engine, volume, locks, and deployment topology are known.

## Migration And Phase Selection

| Change | Safe shape | High-risk condition and proof |
| --- | --- | --- |
| Add optional structure | Additive DDL that old code ignores. | Verify metadata/lock behavior and old/new readers/writers. |
| Add required structure | Add permissive shape, backfill/repair, validate, then enforce. | One-step rewrite/lock or incomplete historical data requires staged proof. |
| Rename/remove structure | Add/bridge new, migrate reads/writes, then remove after consumer and usage evidence. | Direct rename/drop breaks mixed versions or destroys rollback state. |
| Large backfill/purge/archive | Batch by owned partition, checkpoint, pause/throttle, validate completeness, and resume idempotently. | Unbounded locks, lag, partial tenants, retention/erasure, or irreversible deletion need owner escalation. |
| Index/constraint change | Use the engine’s online/deferred validation mechanism when supported. | Lock class, invalid artifact cleanup, duplicate/violation scan, and rollback are unproved. |
| Cross-store cutover | CDC or dual path with lag/reconciliation, bounded divergence, source retention, and cutover reversal. | Unknown writers, missed updates, or incompatible identity/ordering make cutover unsafe. |

| Phase | Required state | Rollback stance |
| --- | --- | --- |
| Expand | New permissive structure and bridge exist; old code still works. | Ignore/drop only after lock and compatibility proof. |
| Migrate | Historical/current writes converge with checkpoint, counts, lag, and reconciliation. | Stop/resume while old reader/source remains valid. |
| Contract | New readers/writers are authoritative; old use is absent by current telemetry and consumer inventory. | Forward-fix or verified restore after the point of no return. |
| Cleanup | Temporary flags, dual paths, checkpoints, indexes, and docs are removed with fresh caller/generated-artifact checks. | Reintroduce only if a live rollback dependency remains. |

## Backfill And Recovery Contract

- Define partition/key progression, sparse-key completion, batch/pause policy, statement/lock timeout, replication/capacity abort signal, checkpoint commit order, retry behavior, and processed/skipped/failed counts.
- For a replayable migration batch, use an explicit predicate or version marker so reruns update rows that still require migration. Define how concurrent writers merge or dual-write. This replay proof does not establish production lock, lag, or capacity safety.
- Classify rollback as additive/code-only, compensating, forward-fix, restore/point-of-no-return, or catastrophic. Name the moment the tier changes and who approves it.
- Restore is evidence only after the relevant backup, permissions, dependency order, integrity check, and measured recovery objective are rehearsed.

## Freshness, Validation, And Routing

| Claim | Required evidence | Proof limit |
| --- | --- | --- |
| Current topology | Schema/migrations, readers/writers, jobs/reports, generated clients, row/write volume, and applied ledger/checksums inspected. | Graph proximity or a prior plan cannot prove no hidden consumer. |
| Lock/load safety | Engine-specific plan/dry run on representative shape, pause threshold, and operator action. | Local empty-schema execution does not prove production lock or saturation. |
| Completeness | Full or partition/tenant counts, constraint/violation queries, CDC lag and reconciliation diff. | “No errors” and samples do not prove all data. |
| Compatibility/rollback | Old/new reader-writer fixtures, deploy order, interruption/resume, compensation or restore rehearsal. | A down script does not prove data recovery or live RTO. |
| Cleanup | Current usage telemetry, caller search, generated artifact refresh, and validation after removal. | Calendar time alone is not a removal gate. |

Route unresolved models and invariants to `data-model-design`, public contracts to `data-api-contract-changer`, and consumers to the compatibility owners. Engine locks and atomicity belong to their datastore and transaction owners. Release, recovery, observability, and regulated-data risks belong to their named specialist gates.

Reject unguarded reruns, direct live-contract renames, one massive mutation, checksum repair before live-state inspection, cleanup without usage evidence, CDC without reconciliation, generated consumers ignored, or rollback claims without recovery proof.
