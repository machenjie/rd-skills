# Data Migration Design Benchmarks And Patterns

Use this reference when `data-migration-design` needs more detail than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, stage fit, evidence, output, routing, and quality gates; use this file for benchmark detail, migration matrices, expand/migrate/contract phase design, checkpoint patterns, rollback tiers, graph/memory/trajectory coupling, validation evidence, and anti-pattern review.

## Benchmark Anchors

- Flyway and Liquibase: versioned migrations, checksum protection, rollback metadata, and repair discipline.
- `gh-ost`, `pt-online-schema-change`, and PostgreSQL `pg_repack`: online DDL and lock avoidance for large tables.
- PostgreSQL concurrent index, `NOT VALID` constraints, validation scans, and MVCC lock behavior.
- Alembic, Django migrations, and ActiveRecord migrations: framework migration ledgers and dependency tracking.
- Debezium, `pgcopydb`, and AWS DMS: CDC-backed cross-system migration and cutover.
- Evolutionary Database Design and expand/contract deployment discipline.
- Google SRE backfill/load-shedding guidance: rate limiting, pause thresholds, and production saturation signals.
- NIST SP 800-34 and ISO 22301: backup verification, restore time objectives, and continuity planning.

## Migration Type Selection Matrix

| Migration type | Tool or pattern | Lock risk | Rollback complexity | Pick when |
| --- | --- | --- | --- | --- |
| Column add, nullable | Native DDL where instant or metadata-only. | Low. | Drop or ignore new column. | New optional structure; old code ignores it. |
| Column add, required | Add nullable, backfill, then validate/enforce required. | Medium to high if done in one step. | Drop column before contract; rollback constraint. | Required field for existing rows. |
| Column rename | Add new, dual-write, migrate reads, drop old after telemetry. | Low per phase. | Remove new or revert reads before contract. | Live systems; never direct rename on hot contract. |
| Column or table drop | Contract phase after zero-use telemetry. | Low lock, high data risk. | Restore or forward-fix after point of no return. | Final cleanup after consumers migrate. |
| Large backfill | Batched job with checkpoint, pause, metrics, and validation. | Row-level locks per batch. | Stop/resume; reverse only if compensating data exists. | Existing data must be transformed at scale. |
| Index creation | `CREATE INDEX CONCURRENTLY`, online schema tool, or background build. | Low to medium; may scan twice. | Drop invalid or new index. | Production query path needs new access path. |
| Constraint tightening | `NOT VALID` constraint, validate later, then enforce. | Scan during validation. | Drop constraint before contract. | Existing rows need repair before enforcement. |
| Cross-DB migration | CDC, dual-read, reconciliation, cutover, source retention. | Low until cutover. | Re-enable source if divergence window is bounded. | Cloud move, service split, monolith decomposition. |
| Purge or archive | Batched move/delete with checkpoint and retention proof. | Row-level locks and vacuum/compaction cost. | Restore from archive/backup or irreversible. | Retention, erasure, or storage pressure. |

## Expand, Migrate, Contract

Use separate deployments when old and new code may coexist.

| Phase | What changes | Required validation | Rollback stance |
| --- | --- | --- | --- |
| Expand | Add nullable column, new table, new index, permissive constraint, or dual-write-ready path. | New structure exists, old code still reads/writes, no hot lock, generated clients unchanged or compatible. | Drop/ignore new structure; code rollback safe. |
| Migrate | Backfill historical data, dual-write, dual-read, repair old records, or run CDC catch-up. | Processed vs expected count, per-tenant/partition completeness, lag below threshold, reconciliation differences. | Stop/resume job; preserve old reader path. |
| Contract | Switch readers to new structure, tighten constraints, remove old writes, then drop old structure. | Zero-use telemetry for old field/table, old code no longer deployed, rollback/forward-fix plan approved. | Usually forward-fix or restore after point of no return. |
| Cleanup | Remove flags, dual-write code, checkpoints, temporary indexes, and docs debt. | Caller search, telemetry, generated artifacts, and validation pass after deletion. | Reintroduce cleanup branch only if rollback dependency remains. |

## Backfill Checkpoint Pattern

```sql
CREATE TABLE IF NOT EXISTS _migration_checkpoint (
  migration_id VARCHAR(100) PRIMARY KEY,
  last_processed_id BIGINT DEFAULT 0,
  processed_rows BIGINT DEFAULT 0,
  failed_rows BIGINT DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Each batch is idempotent: only rows still missing the target value are touched.
UPDATE users
SET new_col = compute_fn(old_col)
WHERE id > :last_processed_id
  AND id <= :last_processed_id + :batch_size
  AND new_col IS NULL;
```

Professional plans also define batch size, pause interval, lock timeout, statement timeout, replication-lag pause threshold, checkpoint commit order, retry policy, and how to detect completion when primary keys are sparse or partitioned.

## Rollback Tier Classification

| Rollback tier | Definition | Recovery action |
| --- | --- | --- |
| Fully reversible | Only new structure is added and old code ignores it. | Drop or ignore new structure; redeploy old code. |
| Code-only rollback | New data exists but old code can safely ignore it. | Redeploy old code and keep additive schema. |
| Compensating migration | New data can be transformed back or reconciled. | Run reviewed reverse migration or compensation job. |
| Forward-fix only | Old state cannot be reconstructed reliably, but new state can be repaired. | Execute pre-reviewed forward-fix and keep old path disabled. |
| Point of no return | Data deleted, old structure dropped, or external cutover completed. | Restore from verified backup or incident response; RTO must be measured. |
| Catastrophic | Data loss with no usable backup or compensation. | Escalate immediately; incident response and postmortem. |

## Graph, Memory, And Trajectory Coupling

Treat repository graph, project memory, and execution trajectory as discovery inputs until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current migrations, schema files, models, readers/writers, jobs, reports, generated clients, and tests are inspected. | Graph proximity is treated as proof that no hidden reader or writer exists. |
| Project memory | Prior migration plan still matches current schema, row volume, code deployment, and consumer topology. | Memory predates a schema change, report/job addition, service split, or generated-client update. |
| Execution trajectory | Validators, builds, migration tests, and generated reports ran after the final migration-skill edit. | Validation predates the final source or reference change. |
| Telemetry and usage history | The metric specifically measures old structure reads/writes over the agreed window. | "No errors" or low traffic is treated as zero-use proof. |
| Migration ledger | Applied versions, checksums, and repair commands match current scripts. | A checksum repair is proposed before verifying live DB state. |

Strong outputs state which graph, memory, telemetry, and trajectory inputs were accepted, rejected, or left unknown.

## Validation Evidence Patterns

- Guard proof: rerun or duplicate deploy attempt skips already-applied work without corrupting state.
- Lock proof: DDL lock class, online option, statement timeout, and dry run against representative schema.
- Backfill proof: concurrent/resume test where interruption resumes from checkpoint without double-processing rows.
- Completeness proof: full-count or partition/tenant validation query, not a sample.
- Compatibility proof: old code reads/writes during expand, new code reads old data, rollback state remains valid.
- Rollback proof: DOWN migration, compensation job, or restore rehearsal with measured RTO.
- Observability proof: processed/updated/skipped/failed counts, lag threshold, duration, and alert/abort signal.
- Cutover proof: CDC lag, reconciliation diff, dual-read comparison, and source re-enable or forward-fix plan.
- Cleanup proof: caller search, telemetry zero-use gate, generated artifact refresh, and validation after removal.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| `ALTER TABLE ... ADD COLUMN ... NOT NULL DEFAULT` on a large hot table. | Rewrite or lock causes production outage. | Add nullable, backfill, validate, then enforce. |
| `ALTER TABLE RENAME COLUMN` on a live contract. | Old readers/writers fail during mixed-version deploy. | Add new, dual-write, migrate reads, drop old later. |
| One massive `UPDATE` or `DELETE`. | Long lock, lag, timeout, partial rollback. | Batches with checkpoint, rate limit, and validation. |
| Migration has no guard and runs twice. | Duplicate data, checksum mismatch, partial state. | Version table, checksum, IF EXISTS/IF NOT EXISTS, idempotent WHERE. |
| Validation says "no errors in logs." | Silent missed tenants or partial rows. | Full completeness queries and per-partition checks. |
| Contract cleanup without zero-use telemetry. | Hidden job/report/consumer breaks after drop. | Usage telemetry, caller search, generated-client review. |
| Restore from backup listed without measured RTO. | Rollback exceeds SLA or restore fails. | Restore rehearsal and point-of-no-return signoff. |
| CDC cutover without reconciliation. | Missed updates or double-writes after source switch. | Dual-read compare, lag threshold, replay plan. |
| Checksum repair before state inspection. | Tool ledger hides drift between scripts and database. | Inspect applied state, repair only after consistency proof. |
| Migration plan ignores generated clients and reports. | Source app passes while downstream contracts break. | Generated artifact diff and consumer/report inventory. |

## Handoff Boundaries

- Use `data-model-design` when the target entity, invariant, relationship, lifecycle, or source of truth is unresolved.
- Use `version-compatibility` or `data-api-contract-changer` when readers, writers, generated clients, events, or API consumers may break.
- Use `relational-database` or `nosql-database` when storage-engine-specific DDL, locks, indexes, partitions, TTL, or consistency settings dominate.
- Use `transaction-consistency` when atomicity, isolation, lock ordering, outbox, or compensation drives migration correctness.
- Use `release-rollback` and `delivery-release-gate` when deployment order, rollback trigger, release owner, canary, or post-release watch is unresolved.
- Use `backup-recovery` when restore, RTO/RPO, backup verification, or retention proof is the primary question.
- Use `security-privacy-gate` when destructive, tenant, regulated, personal, audit, or financial data is affected.
- Use `reliability-observability-gate` when production lag, lock wait, queue depth, capacity, SLO, or alerting remains unowned.
