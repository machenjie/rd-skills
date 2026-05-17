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

# Industry Benchmarks

Anchor against: **Flyway** (Redgate) — versioned migration with checksum-protected SQL and Java migrations; `V{version}__{description}.sql` naming convention. **Liquibase** — XML/YAML/SQL changelog with rollback support and `dbDoc`. **`gh-ost`** (GitHub Online Schema Change) — online MySQL DDL without metadata lock; triggers-free, testable on replica first. **`pt-online-schema-change`** (Percona Toolkit) — MySQL online DDL with trigger-based sync. **PostgreSQL `pg_repack`** — online table reorganization without exclusive locks. **Django migrations** / **Alembic (SQLAlchemy)** / **ActiveRecord migrations** — framework-level migration execution and dependency tracking. **`pgcopydb`** — PostgreSQL online copy with change data capture for large-table migrations. **Debezium / CDC (Change Data Capture)** — event-based data migration for dual-write or cross-system migration. **Martin Fowler "Evolutionary Database Design"** (Sadri & Sadalage) — expand-contract pattern. **Sam Newman "Monolith to Microservices"** Ch. 4 — database decomposition and Strangler Fig pattern for data migration. **Google SRE Book** Ch. 30 (Dealing with Cascading Failures) — rate limiting and load shedding during backfills. **NIST SP 800-34** — contingency planning including data backup verification. **ISO 22301** — business continuity; restore time objective (RTO) for data recovery. **AWS Database Migration Service (DMS)** — source-to-target CDC for cross-cloud migrations. **Zero-downtime deployment** discipline: traffic must be serveable during every migration phase.

### Migration Type Selection Matrix

| Migration type | Tool / pattern | Lock risk | Rollback complexity | Pick when |
| --- | --- | --- | --- | --- |
| **Column add (nullable)** | Native DDL (PostgreSQL ≥ 11: instant) | None/minimal | Drop column | Greenfield; no data needed |
| **Column add (NOT NULL + default)** | Add nullable → backfill → add constraint | Table rewrite if < PG 11 | Drop column; rollback constraint | Adding required field to existing table |
| **Column rename** | Expand: add new → dual-write → migrate reads → drop old | None per phase | Remove new; revert writes | Never: `ALTER TABLE RENAME COLUMN` in one step on live table |
| **Column drop** | Contract phase only after 2 prior deployments | None | Restore from backup | Final cleanup after expand-migrate confirmed |
| **Large backfill** | Batched UPDATE with checkpoint table; `pg_background` / background job | Row-level locks per batch | Mark column nullable; read as NULL | > 100K rows; production table |
| **Index creation** | `CREATE INDEX CONCURRENTLY` (PostgreSQL) / `pt-online-schema-change` (MySQL) | None (concurrent) | `DROP INDEX` | Any production index; avoids share lock |
| **Table rename / restructure** | Expand: new table → dual-write → migrate reads → deprecate old | None per phase | Re-enable old reads | Cross-service; data model refactor |
| **Cross-DB migration** | CDC (Debezium) → dual-read → validate → cutover | None until cutover | Re-enable source | Monolith decomposition; cloud migration |
| **Schema version migration** | Flyway/Liquibase with explicit version | Per migration script | `flyway repair` + compensating | Standard versioned schema evolution |
| **Data purge / archive** | Batched DELETE with checkpoint; move to archive table first | Row-level per batch | Cannot un-delete without backup | GDPR erasure; retention enforcement |

### Expand-Migrate-Contract Phases

```
Phase 1: EXPAND
  - Add nullable column / new table / new index
  - Old code: reads and writes old structure ✅
  - New code: not yet deployed
  - Validation: new structure exists; old reads still pass; zero null impact on writes

Phase 2: MIGRATE (may be split into deploy + background backfill)
  - Deploy code that writes BOTH old and new structure (dual-write)
  - Run batched backfill of historical data
  - Validation: backfill 100% complete; no null values in new column for required fields

Phase 3: CONTRACT (only after code cutover confirmed)
  - Deploy code that reads ONLY new structure
  - Remove old structure (column, table, index) in a separate migration
  - Validation: zero reads of old column in APM/query logs for ≥ 24h
  - Cleanup: remove dual-write code; drop old column/table
```

### Backfill Checkpoint Pattern

```sql
-- Checkpoint table: tracks last processed primary key
CREATE TABLE IF NOT EXISTS _migration_checkpoint (
  migration_id VARCHAR(100) PRIMARY KEY,
  last_processed_id BIGINT DEFAULT 0,
  processed_rows BIGINT DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Backfill loop (application-level or stored procedure)
LOOP
  SELECT last_processed_id INTO v_checkpoint FROM _migration_checkpoint WHERE migration_id = 'backfill_new_col_v1';
  
  UPDATE users
  SET new_col = compute_fn(old_col)
  WHERE id > v_checkpoint AND id <= v_checkpoint + 1000
    AND new_col IS NULL;  -- idempotent: skip already-migrated rows
  
  -- Checkpoint after each batch
  UPDATE _migration_checkpoint SET last_processed_id = v_checkpoint + 1000, processed_rows = processed_rows + ROW_COUNT();
  
  EXIT WHEN v_checkpoint >= (SELECT MAX(id) FROM users);
  PERFORM pg_sleep(0.05);  -- rate limit: 50ms pause between batches
END LOOP;
```

### Rollback Tier Classification

| Rollback tier | Definition | Recovery action |
| --- | --- | --- |
| **Fully reversible** | Structure added; no data changed; old code unaffected | Drop new column/table; re-deploy old code |
| **Code-only rollback** | Old code deployed; dual-write disabled; new column ignored | Re-deploy old code; new column stays (nullable; benign) |
| **Compensating migration** | New column written; can write reverse migration | Run reverse UPDATE/backfill to undo writes; deploy old code |
| **Point of no return** | Old column dropped; data deleted | Restore from last verified backup; measure RTO explicitly |
| **Catastrophic (irreversible)** | Data deleted with no backup window | Escalate immediately; incident response; post-mortem |

# Selection Rules

Select this capability when **existing stored data or schema must change** in a live system. Adjacent routing:

- Prefer `data-model-design` when designing the target schema before planning the migration path.
- Prefer `version-compatibility` when the primary concern is old and new code versions coexisting during rollout.
- Prefer `relational-database` or `nosql-database` for storage-specific physical design decisions (index type, partitioning strategy, storage engine).
- Prefer `backup-recovery` when restore procedures and RTO/RPO guarantees are the primary concern.

# Risk Escalation Rules

Escalate when: migration is destructive (column drop, data deletion, truncation) and backup has not been verified; migration touches financial records, audit logs, personal data (GDPR right to erasure), or regulatory data; migration exceeds 10M rows and no batching plan exists; migration requires DDL on a table with > 1K transactions/second; migration runs in a 30-minute deployment window but estimated backfill is 6 hours; rollback would require a backup restore with RTO > SLA; a cross-service migration requires multiple teams to coordinate deployment ordering; schema registry (Confluent, Glue) compatibility mode change is required as part of the migration.

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

- DDL on hot table causes metadata lock; application requests queue; timeout cascade.
- New column deployed without backfill; code reads NULL unexpectedly; NullPointerException in production.
- Old column dropped before all service instances upgraded; instances on old code crash.
- Backfill not resumable; interrupted at row 500K of 2M; restarts from row 0; double-processes 500K rows.
- Migration runs twice (re-deploy scenario); duplicate unique key; migration fails mid-flight; DB in partial state.
- Validation check samples 1K rows; 200K rows for specific tenant failed backfill; discovered 3 months later.
- `CREATE INDEX` takes share lock; deploys during peak traffic; 2-minute outage.
- Compensating rollback migration does not match forward migration; data left in inconsistent state.
- Replication lag grows during backfill; replica-connected reporting service serves stale data; reports silently wrong.
- Feature flag not set; new-column reads deployed before backfill complete; returns NULL for 30% of users.
- `pg_dump` backup taken before migration but not verified; restore fails; point-of-no-return with no rollback.
- Cross-service migration: service A drops column before service B is updated; service B crashes on reads.

# Output Contract

Return a migration plan with:

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

# Used By

- data-api-contract-changer
- delivery-release-gate
- data-middleware-change-builder

# Handoff

Hand off to `version-compatibility` for mixed-version deployment coordination; `data-model-design` for target model design; `delivery-release-gate` for deployment scheduling and rollout sequencing; `data-middleware-change-builder` for storage-engine-specific execution details; `backup-recovery` for restore procedure validation.

# Completion Criteria

The capability is complete when **every phase of the migration can be executed against a production-scale dataset with observable progress, guaranteed idempotency, a credible rollback plan, and zero unplanned downtime from lock contention** — with validation evidence proving completeness before dependent code is deployed.
