---
name: data-migration-design
description: Designs guarded, observable, rollback-aware, deployment-order-aware data migrations and backfills that can run safely on live systems without silent partial application, data loss, or avoidable downtime.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "30"
changeforge_version: 0.1.0
---

# Mission

Design data migrations that are **guarded against duplicate execution, observable at every phase, interruptible and resumable at production scale, deployment-sequence-aware across expand/migrate/contract phases, rollback-planned even when fully reversible is impossible, and validated by evidence rather than assumption** — so that a schema or data change can be applied to a live system without downtime, data loss, lock-induced outage, or silent partial application.

# When To Use

Use this capability when a change: adds, drops, renames, or alters a column, table, index, partition, constraint, or view; backfills new columns or calculated fields from existing data; migrates data between storage systems (relational → document, on-prem → cloud, monolith → microservice); reindexes or re-shards data; transforms field formats (date format normalization, UUID generation, enum code migration); archives or purges data at scale; repairs data integrity violations; or introduces a new schema version alongside an existing one.

# Do Not Use When

Do not use this capability for application-level business logic changes that do not alter stored data or schema. Do not use it to design the target data model — use `data-model-design` first, then return here for the migration plan. Do not use it to authorize destructive operations — escalate to the risk escalation rules first.

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release, and handoff when stored data, migration evidence, or a remembered migration claim can affect compatibility, rollback, lock risk, partial application, or production release safety.

Own migration design during planning, implementation review, testing, and release preparation when stored data, schema, indexes, constraints, partitions, backfills, purges, or cross-system cutovers change. In planning, turn current schema, migrations, generated clients, repository graph, project memory, execution trajectory, row-count evidence, deployment topology, and validation history into an expand/migrate/contract plan before implementation. In review, reject stale "no readers", "safe DDL", "already backfilled", "rollback is restore", or "migration passed once" claims unless current source, telemetry, and validation confirm them. Hand off when the unresolved decision is target data model, API/DTO compatibility, storage-engine execution, release sequencing, backup restore, security/privacy, or production observability.

# Non-Negotiable Rules

- **Migrations are idempotent or guarded.** Running a migration twice must produce the same correct outcome — either via idempotency (`IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, upsert logic) or via execution guards (migration versioning table, Flyway/Liquibase checksum, custom guard row). An unguarded migration that errors on second run is not guarded.
- **Expand-migrate-contract sequencing.** Schema changes that break old code must be split into at least three independent deployments: (1) **Expand** — add new structure (nullable column, new table, new enum value) without removing old; (2) **Migrate** — backfill data into new structure; old code still works against both; (3) **Contract** — remove old structure only after code cutover is confirmed and telemetry shows zero reads of old structure. Never remove a column in the same deployment that adds the replacement.
- **No long-running locks on production hot tables.** `ALTER TABLE ... ADD COLUMN` with a non-null default rewrites the entire table in PostgreSQL < 11 (in PostgreSQL ≥ 11, nullable defaults are instant; NOT NULL defaults are not). `ALTER TABLE ... ADD COLUMN ... NOT NULL DEFAULT x` under lock will outage a hot table. Use: nullable column first, backfill, add NOT NULL constraint separately with a concurrent index or `SET NOT NULL` validation check in PostgreSQL. MySQL DDL operations without `pt-online-schema-change` or `gh-ost` take a metadata lock.
- **Backfills are batched, rate-limited, and checkpointed.** Never `UPDATE users SET new_col = fn(old_col)` as a single statement at scale. Batch by primary key or partition: process N rows, checkpoint the last processed ID, pause, repeat. Rate limit to avoid replication lag or I/O saturation. Resumable from checkpoint without re-processing completed rows.
- **Migrations are observable.** At minimum: row count processed vs expected, error count, elapsed time, estimated completion, replication lag (if applicable), lock wait events. Progress must be readable by the on-call engineer without grepping logs.
- **Rollback is planned before execution, not after failure.** For each migration phase: what does rollback look like? (restore from backup? compensating migration? disable code that reads new column?). If full rollback is impossible (data deleted, column dropped), document the point of no return explicitly and require explicit sign-off.
- **Validation queries run before and after each phase.** Pre-condition checks: row count, data integrity, referential integrity, constraint validity. Post-condition checks: new column not-null rate, backfill completeness query, constraint violation scan. Not sampling — full count or partition scan.
- **Destructive operations require runbook approval.** Dropping a column, truncating a table, or deleting data at scale requires: a recorded dry-run count, an owner sign-off, a backup verification, and a rollback plan with tested restore time.
- **Migrations are deployment-environment-aware.** A migration that uses `gh-ost` on production may need `pt-online-schema-change` on staging (different MySQL minor version). Migration tooling versions, target DB versions, and replication topology must match between test and production environments.

# Mode Matrix

Select the migration mode before choosing DDL, backfill, cutover, validation, or rollback mechanics.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Additive schema expand | Nullable column, new table, new index, new constraint, or safe structure added for future code. | Preserve old readers/writers and avoid hot-table locks. | Current schema, old/new code compatibility, lock class, online DDL option, rollback as ignore/drop. | `data-model-design`, `relational-database`, `version-compatibility` | Contract cleanup in same deploy. |
| Batched backfill or data repair | Existing rows need computed values, normalization, repair, archive, or purge. | Make the work resumable, observable, rate-limited, and tenant/partition complete. | Row counts, batch/checkpoint plan, lag threshold, validation query, retry/resume proof. | `transaction-consistency`, `data-side-effect-flow-tracing`, `quality-test-gate` | Single unbounded UPDATE/DELETE. |
| Destructive contract cleanup | Drop/rename column, remove table/index, add NOT NULL, tighten constraint, or delete data. | Prove all old readers/writers are gone and rollback point is explicit. | Telemetry zero-use gate, backup/restore proof, owner signoff, rollback tier. | `release-rollback`, `delivery-release-gate`, `backup-recovery` | Destructive change before telemetry. |
| Cross-system migration or cutover | CDC, dual-write, dual-read, source-to-target copy, service split, cloud migration, or sharding. | Keep source of truth, reconciliation, cutover, and rollback clear. | Source/target ownership, CDC lag, consistency check, cutover criteria, forward-fix plan. | `data-api-contract-changer`, `message-queue-design`, `reliability-observability-gate` | Big-bang cutover without dual-read or reconciliation. |
| Operational migration repair | Failed, partial, slow, duplicate, checksum-mismatched, or interrupted migration. | Verify actual state before repair and avoid repeated blind reruns. | Migration ledger, partial row counts, same-pattern scan, repair script, revalidation output. | `failure-diagnosis`, `agent-execution-discipline`, `regression-testing` | Third same-path retry. |
| Handoff closure | final answer, review, release note, or incident closure claims migration readiness. | Map every migration claim to fresh validator/test/report evidence and explicit unknowns. | changed migration-to-validation map, exit codes, artifact/report paths, evidence limits. | `plan-execution-consistency`, `validation-broker`, `quality-test-gate` | Completion language without migration claim. |

# Industry Benchmarks

Anchor against versioned migration tools, online DDL practice, expand/migrate/contract, batched and checkpointed backfills, CDC and dual-read cutovers, backup/restore continuity standards, zero-downtime deployment, and SRE rate limiting during production data work. Keep this body focused on stage fit, routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for migration-type matrices, EMC phase detail, checkpoint patterns, rollback tiers, graph/memory/trajectory coupling, validation evidence, and anti-pattern detail.

# Selection Rules

Select this capability when **existing stored data or schema must change** in a live system. Adjacent routing:

- Prefer `data-model-design` when designing the target schema before planning the migration path.
- Prefer `version-compatibility` when the primary concern is old and new code versions coexisting during rollout.
- Prefer `relational-database` or `nosql-database` for storage-specific physical design decisions (index type, partitioning strategy, storage engine).
- Prefer `backup-recovery` when restore procedures and RTO/RPO guarantees are the primary concern.

# Risk Escalation Rules

Escalate when: migration is destructive (column drop, data deletion, truncation) and backup has not been verified; migration touches financial records, audit logs, personal data (GDPR right to erasure), or regulatory data; migration exceeds 10M rows and no batching plan exists; migration requires DDL on a table with > 1K transactions/second; migration runs in a 30-minute deployment window but estimated backfill is 6 hours; rollback would require a backup restore with RTO > SLA; a cross-service migration requires multiple teams to coordinate deployment ordering; schema registry (Confluent, Glue) compatibility mode change is required as part of the migration.

# Proactive Professional Triggers

- **Signal:** project memory, repository graph, or prior execution says there are "no readers", a backfill is "done", a DDL is "safe", or rollback is "just restore" without current confirmation. **Hidden risk:** stale evidence green-lights destructive or mixed-version-unsafe migration work. **Required professional action:** confirm current schema, migrations, code readers/writers, generated clients, query/report consumers, telemetry, and validation freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limits, and unknown consumer disclosure.
- **Signal:** DDL touches a hot table, large table, NOT NULL/default, foreign key, unique constraint, enum, index, partition, or table rewrite. **Hidden risk:** metadata locks, table scans, replication lag, or query-plan regression cause outage. **Required professional action:** identify lock class and online alternative before execution. **Route to:** `relational-database`, `indexing-query-optimization`, `reliability-observability-gate`. **Evidence required:** row/write volume, lock analysis, online DDL choice, timeout/abort threshold, dry-run or not-verified limit.
- **Signal:** backfill, purge, repair, archive, or data transform is unbatched, uncheckpointed, unbounded, or tenant/partition blind. **Hidden risk:** partial application, duplicate processing, lag spike, or missed tenant data. **Required professional action:** require batch/checkpoint/rate-limit/resume and full validation queries. **Route to:** `transaction-consistency`, `data-side-effect-flow-tracing`, `quality-test-gate`. **Evidence required:** checkpoint store, idempotent WHERE clause, progress metrics, per-partition validation.
- **Signal:** drop, rename, data delete, constraint tightening, or contract cleanup is proposed before telemetry proves old usage is gone. **Hidden risk:** old code, reporting, jobs, or external consumers break during rollback or mixed-version window. **Required professional action:** enforce expand/migrate/contract and classify rollback tier. **Route to:** `version-compatibility`, `release-rollback`, `delivery-release-gate`. **Evidence required:** old/new compatibility matrix, zero-use telemetry gate, owner signoff, rollback or forward-fix plan.
- **Signal:** migration crosses systems, uses CDC, dual-write, dual-read, service decomposition, source-to-target sync, or cutover. **Hidden risk:** source-of-truth ambiguity, ordering drift, missed updates, and rollback data divergence. **Required professional action:** define source/target ownership, reconciliation, cutover window, and post-cutover validation. **Route to:** `data-api-contract-changer`, `message-queue-design`, `reliability-observability-gate`. **Evidence required:** CDC lag, consistency query, replay/reconciliation plan, cutover abort criteria.
- **Signal:** migration touches financial, audit, PII/regulated, tenant boundary, or deletion/retention data. **Hidden risk:** legal/compliance harm or unrecoverable customer data loss. **Required professional action:** classify data and require security/privacy, backup, and approval evidence. **Route to:** `security-privacy-gate`, `backup-recovery`, `delivery-release-gate`. **Evidence required:** data classification, retention/deletion rule, backup restore proof, approval owner.

# Critical Details

Data migrations are among the highest-risk operations in a production system. Precision failures that cause incidents:

- **PostgreSQL `NOT NULL DEFAULT` at scale.** In PostgreSQL < 11, `ALTER TABLE ADD COLUMN ... NOT NULL DEFAULT 'x'` rewrites the entire table (full table lock). In PostgreSQL ≥ 11, adding a column with a non-volatile constant default is instant (stored in catalog). Adding `NOT NULL` constraint without a `DEFAULT` on an existing table still requires a table scan. Always test on a restored production-sized copy before running live.
- **Replication lag amplification.** Large backfills increase binary log / WAL volume dramatically. Monitor `pg_stat_replication.write_lag` / `replay_lag`; pause backfill if lag exceeds threshold. On MySQL RDS/Aurora, read-replica lag affects read-after-write consistency for applications relying on replicas.
- **Concurrent index creation on PostgreSQL.** `CREATE INDEX CONCURRENTLY` does not take a share lock but does two table scans. It can fail partway through (leaving an `INVALID` index in `pg_indexes`). Always check for invalid indexes after concurrent index creation: `SELECT * FROM pg_indexes WHERE indexdef LIKE '%invalid%'` (check `pg_class.indisvalid`).
- **Migration tool checksum mismatch.** Flyway checksums prevent replaying modified scripts. Editing a previously-applied migration file causes `ERROR: Checksum mismatch for migration V5__add_index.sql`. Use `flyway repair` only after confirming the script is idempotent and the production state is consistent.
- **Feature flag gate for new column reads.** Deploy a feature flag that gates new-column reads; backfill completes; validate completeness; then enable flag. Allows instant rollback without a new deployment.
- **Dual-write consistency.** During dual-write phase, a failure after writing old but before writing new produces an inconsistent record. Use a transaction covering both writes where possible, or accept eventual consistency with a reconciliation job.
- **Zero-downtime constraint addition.** In PostgreSQL, `ALTER TABLE ADD CONSTRAINT ... NOT VALID` adds the constraint without scanning existing rows. `ALTER TABLE VALIDATE CONSTRAINT` runs the scan separately as a lower-impact operation. This pattern avoids a full-table lock when adding a foreign key or check constraint to a large table.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `ALTER TABLE orders ADD COLUMN status VARCHAR NOT NULL DEFAULT 'pending'` on PG 10 | Full table rewrite; table locked for minutes; production outage |
| `UPDATE users SET new_col = compute(old_col)` in one transaction | Locks 10M rows for 45 minutes; replication lag spikes; timeout; partial rollback |
| Deploy new code + drop old column in one deployment | Old code on running instances reads dropped column; crashes immediately |
| No migration guard; migration runs twice | Duplicate data inserted; constraint violation; inconsistent state |
| Validation: "no errors in logs" | Partial backfill (failed tenants) passes log check; new column NULL for 5% of users |
| Rollback plan: "restore from backup" with untested RTO | Backup restore requires 4 hours; SLA is 30 minutes; plan is not credible |
| `CREATE INDEX` without `CONCURRENTLY` on production | Share lock prevents writes; downtime |
| Backfill runs at full speed without rate limit | Replication lag grows to 2 hours; read replicas serve stale data; reports fail |

# Failure Modes

- **Hot-table lock:** DDL on hot table causes metadata lock; application requests queue; timeout cascade.
- **Unbackfilled read:** new column deploys without backfill; code reads NULL unexpectedly; NullPointerException in production.
- **Mixed-version crash:** old column drops before all service instances upgrade; old code crashes.
- **Non-resumable backfill:** interrupted at row 500K of 2M; restart begins at row 0 and double-processes 500K rows.
- **Duplicate execution:** migration runs twice during redeploy; duplicate unique key fails mid-flight and leaves partial state.
- **Sample-only validation:** 1K sampled rows pass while 200K rows for one tenant failed backfill; defect is discovered months later.
- **Blocking index build:** `CREATE INDEX` takes a share lock during peak traffic and causes outage.
- **Bad compensation:** rollback migration does not match forward migration; data remains inconsistent.
- **Replica lag:** backfill grows replication lag; replica-connected reporting service serves stale data and reports silently wrong.
- **Premature flag enablement:** new-column reads deploy before backfill completes; 30% of users receive NULL-derived behavior.
- **Untested restore:** `pg_dump` backup exists but restore fails; point-of-no-return has no credible rollback.
- **Cross-service ordering break:** service A drops column before service B is updated; service B crashes on reads.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 migration selection, safety, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete migration plan, before implementation starts, or when batching, rollback, observability, cleanup, or owner signoff is uncertain. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when migration-type selection, EMC phase detail, checkpoint SQL, rollback tiers, graph/memory/trajectory reuse, validation evidence, or anti-pattern detail needs depth. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.
Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on migration-to-validation mapping, stale graph/memory/execution claims, tool permission boundaries, production evidence limits, or final handoff readiness.

# Output Contract

Return a migration plan with:

- `mode_selected` (additive schema expand, batched backfill/data repair, destructive contract cleanup, cross-system migration/cutover, operational migration repair)
- `migration_evidence` (current schema, migration ledger, code readers/writers, generated clients, reports/jobs, repository graph, project memory, execution trajectory, validation freshness, and row-count/volume evidence inspected)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for every graph/memory/trajectory claim that affects safety)
- `migration_type` (DDL schema, data backfill, cross-system, purge/archive, constraint add, index creation)
- `affected_objects` (tables, columns, indexes, constraints, partitions with row-count estimates)
- `phases` (per phase: name, description, code-deploy order, migration script, validation queries, duration estimate)
- `deployment_sequence` (phase → deploy order: expand deploy number, migrate deploy number, contract deploy number)
- `guards` (idempotency mechanism: IF NOT EXISTS, migration table, Flyway checksum)
- `lock_analysis` (per DDL statement: lock type, lock duration estimate, mitigation: CONCURRENTLY, gh-ost, NOT VALID)
- `batching_plan` (batch size, checkpoint mechanism, pause interval, total batches, estimated wall time)
- `observability` (progress metric name, dashboard, replication lag threshold, alerting trigger)
- `validation_queries` (pre-condition queries, post-condition queries, completeness check queries)
- `rollback_tier` (per phase: fully reversible / code-only / compensating / point-of-no-return)
- `rollback_steps` (per phase: exact steps, estimated time, dependencies)
- `backup_verification` (snapshot taken before destructive phase, restore tested, RTO measured)
- `feature_flag` (gate name for new-column reads; enable condition: backfill complete + validated)
- `owner` (migration owner, on-call contact, change approval record)
- `runbook_steps` (execute steps for each phase with expected outputs and abort criteria)
- `cleanup_criteria` (what telemetry must show before old structure is dropped)
- `changed_migration_to_validation_map` (each phase, DDL, backfill, reader/writer, guard, validation query, rollback step, and cleanup gate mapped to validator or residual risk)
- `handoff_boundaries` (what belongs to data model, API/DTO compatibility, relational/NoSQL execution, release sequencing, backup restore, security/privacy, reliability/observability, or no-next-gate rationale)
- `evidence_limits` (what was not verified, such as unknown consumers, production cardinality, lock contention, replica lag, restore RTO, CDC replay, or hidden reports/jobs)

# Evidence Contract

Close a migration plan only when the output names selected mode, current migration evidence inspected, graph/memory/execution reuse judgment, affected objects and volumes, old/new reader-writer compatibility, phase order, guard/idempotency strategy, lock and batch analysis, validation queries, rollback tier and steps, backup/restore proof when destructive, observability and abort criteria, changed-migration-to-validation map, reuse / placement rationale, behavior preservation, what evidence proves, what evidence does not prove, next gate, handoff boundaries, residual risk, and evidence limits. A migration plan that says "run migration, monitor logs, restore backup if needed" is not sufficient evidence.

# Benchmark Coverage

Improved migration plans should reject one-step rename/drop, NOT NULL/default hot-table rewrites, unbounded UPDATE/DELETE, missing migration guards, sampling-only validation, publish/reader cutover before backfill completion, "restore from backup" without measured RTO, checksum repair without state verification, and contract cleanup without telemetry proving old usage is gone. Detailed matrices and examples belong in references so this body stays efficient.

# Routing Coverage

Route here when the primary work is live stored-data or schema change sequencing: DDL safety, backfill, checkpointing, validation, rollback tier, EMC phases, migration ledger, or cutover. Hand off when the primary concern is target model design (`data-model-design`), client-visible compatibility (`version-compatibility`, `data-api-contract-changer`), storage-engine physical execution (`relational-database` or `nosql-database`), backup restore/RTO (`backup-recovery`), release rollout (`delivery-release-gate` or `release-rollback`), security/privacy of data (`security-privacy-gate`), or production telemetry (`reliability-observability-gate`).

# Quality Gate

The migration plan passes only when:

1. Every migration phase is idempotent or guarded against duplicate execution.
2. Expand-migrate-contract phases are in separate deployments when old and new code must coexist.
3. No DDL statement takes an exclusive table lock on a production hot table without an online DDL alternative.
4. Backfill is batched with a checkpoint mechanism; resumable without re-processing completed rows.
5. Validation queries cover 100% of affected rows (not sampling) for each phase.
6. Rollback tier is explicitly classified per phase; point-of-no-return is marked with owner sign-off.
7. For destructive phases: backup taken, restore tested, and RTO measured before execution.
8. Migration progress is observable by on-call engineer in real time without grepping logs.
9. Replication lag monitoring is active during backfill with a pause threshold.
10. Feature flag or equivalent gates new-column reads until backfill is validated as complete.
11. Repository graph, project memory, and execution trajectory inputs are current-source confirmed or marked not verified before they shape migration safety decisions.
12. Old and new readers/writers, generated clients, reports, jobs, and rollback paths are compatible for every expand/migrate/contract phase or explicitly handed off to compatibility/release gates.
13. Every DDL, backfill, validation, guard, observability, rollback, and cleanup decision maps to validation evidence or named residual risk.
14. Destructive or irreversible phases have data classification, backup/restore evidence, owner signoff, and point-of-no-return disclosure before execution.
15. Handoff boundaries and evidence limits are explicit so migration design is not over-claimed as target model approval, consumer compatibility proof, production release readiness, or backup-recovery proof.

# Used By

- data-api-contract-changer
- delivery-release-gate
- data-middleware-change-builder

# Handoff

Hand off to `version-compatibility` for mixed-version deployment coordination; `data-model-design` for target model design; `delivery-release-gate` for deployment scheduling and rollout sequencing; `data-middleware-change-builder` for storage-engine-specific execution details; `backup-recovery` for restore procedure validation.

# Completion Criteria

The capability is complete when **every phase of the migration can be executed against a production-scale dataset with observable progress, guaranteed idempotency, a credible rollback plan, and zero unplanned downtime from lock contention** — with validation evidence proving completeness before dependent code is deployed.
