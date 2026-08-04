# Data Migration Evidence Patterns

Use this reference when migration closure depends on repository inspection and prior task evidence, execution output, validation freshness, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second migration tutorial.

## Migration-To-Validation Map

| Migration claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current schema and migration ledger are known | Schema files, applied migration list, generated clients, and migration checksums inspected | The plan targets the inspected source state | Hidden manual DB drift or uninspected downstream stores |
| Old and new code can coexist | Expand/migrate/contract compatibility matrix plus reader/writer inventory | Inspected versions can run in the stated deployment order | Unknown consumers, mobile lag, or external reports are safe |
| DDL avoids unsafe locks | Lock class, online DDL choice, timeout/abort threshold, and representative dry-run or explicit not-verified limit | The selected DDL path has a bounded lock strategy | Actual production lock contention or peak traffic impact |
| Backfill is resumable | Batch, checkpoint, idempotent predicate, interruption/resume test, and progress metric | Tested job can resume without double-processing the covered rows | Sparse partitions, all tenant distributions, or full production runtime |
| Validation covers affected data | Full-count, partition, or tenant validation query with expected and actual counts | Inspected affected rows satisfy the declared invariant | Future writes, late CDC events, or hidden consumer transforms |
| Rollback tier is credible | Per-phase rollback tier, command/test/report, owner signoff, and point-of-no-return note | The named phase has a reviewed recovery path | Restore RTO, provider SLA, or manual runbook reliability unless rehearsed |
| Destructive cleanup is safe | Caller search, generated artifact diff, zero-use telemetry gate, backup/restore evidence, and signoff | Inspected old readers/writers are gone before deletion | Uninstrumented jobs, ad hoc queries, or offline archives are safe |
| Cross-system cutover is bounded | Source-of-truth decision, CDC lag, reconciliation diff, replay/abort plan, and post-cutover validation | Source/target divergence is measured for the inspected cutover | Long-tail event order, all regions, or uninspected repair jobs |
| Release watch can detect harm | Lag, lock wait, error, throughput, duration, and completeness metrics with owner and threshold | Operators can see expected migration failure signals | Thresholds are sufficient for every production seasonality pattern |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, previous migration notes, runbooks, dashboards, and old validation reports as discovery inputs until current source confirms them.
- Accept a prior claim only while the schema, migration scripts, generated clients, reports or jobs, row volumes, deployment order, and validation command match current state. Examples include "no readers", "backfill done", "safe DDL", "rollback tested", and "ledger repaired".
- Mark evidence stale after edits to migration files, schema, generated clients, fixtures, release sequence, feature flags, validation queries, reports, or build/install outputs.
- Record inspected and skipped consumers: application readers/writers, generated clients, reports, jobs, ETL, dashboards, external integrations, and manual query surfaces.
- When making a final migration-safety claim about the current migration, map it to a command, test, validator, report, migration dry run, telemetry query, restore rehearsal, or explicit not-run residual risk.

- If migration dry run against local or throwaway DB, record dataset, cleanup, reset, and absence of production credentials.
- If production DB, CDC, backup, restore, cloud, or deploy command, require permission, dry-run when available, rollback/forward-fix path, stop condition, and redaction rule.
- If telemetry, dashboard, or audit export, redact tenant/user/secret-bearing values and state retention limits.
