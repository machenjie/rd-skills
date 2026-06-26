---
name: sql-professional-usage
description: Use when writing or reviewing SQL for application queries, migrations, reports, or analytics with focus on transaction safety, indexing, query plans, locks, pagination, null semantics, timezones, data correctness, injection safety, and migration compatibility.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "96"
changeforge_version: 0.1.0
---

# Mission

Enforce professional SQL usage for application queries, migrations, reports, and analytics: parameterized queries, plan-verified indexes, bounded and stable pagination, explicit NULL / timezone / numeric-precision semantics, lock-aware migrations, expand-contract delivery, and fresh source evidence before relying on repository graph, project memory, or prior execution claims. Reject string-composed queries, plan-unverified "it works locally" changes, and migrations that hold long locks on production tables.

# Tooling Baseline (SQL)

- **Engine lifecycle**: use a vendor-supported engine version approved by the target project. If a Postgres, MySQL, SQLite, cloud warehouse, or managed database version is EOL, preview-only, unsupported by the driver, or conflicts with the project's platform policy, record the project rule and update this capability before treating the baseline as current.
- **Engine evidence**: Postgres uses `psql --no-psqlrc`, `EXPLAIN (ANALYZE, BUFFERS, VERBOSE)`, `pg_stat_statements`, and `auto_explain`; MySQL uses `EXPLAIN ANALYZE`, `performance_schema`, `sys`, and lock/deadlock reports; SQLite requires `PRAGMA foreign_keys=ON`, WAL when concurrent reads/writes matter, and a busy timeout.
- **SQL format and migration tooling**: `sqlfluff` with dialect set, `pgFormatter` for Postgres where used, and project-approved tools such as Flyway, Liquibase, Atlas, golang-migrate, Alembic, Prisma Migrate, or Rails ActiveRecord. Migrations are versioned, idempotent where supported, and reviewed.
- **Online schema change (large tables)**: `gh-ost` or `pt-online-schema-change` (MySQL); `pg_repack` (Postgres) for table rewrites; concurrent index builds (`CREATE INDEX CONCURRENTLY` in Postgres, `ALTER TABLE ... ALGORITHM=INPLACE, LOCK=NONE` in MySQL 8).
- **Query observability**: `pg_stat_statements` + `auto_explain.log_min_duration` (Postgres); `slow_query_log` + `performance_schema.events_statements_summary_by_digest` (MySQL).
- **Drivers and pools**: require driver-native parameters (`psycopg`, `asyncpg`, `pgx`, Rust `sqlx`, `node-postgres`, JDBC `PreparedStatement`) and pool sizing via Little's Law; never unbounded.

# When To Use

Use when SQL queries, migrations, reports, analytics, indexes, transaction behavior, lock behavior, pagination, or database-backed correctness change. Use whenever an `EXPLAIN` plan is needed; whenever a migration touches a table with > 1M rows; whenever a query joins > 2 tables or filters/sorts on un-indexed columns.

# Do Not Use When

Do not use as a syntax lesson. Do not use to bypass `data-migration-design` (schema-evolution planning) or `transaction-consistency` (isolation / two-phase) when the change is structurally about those.

# Stage Fit

Use during implementation planning, coding, bug-fix, code-review, refactoring, and testing. Per-stage focus:

- **coding**: parameterization, set-based logic, explicit columns, transaction isolation, index-aware predicates.
- **debugging-diagnosis**: missing/unused index, lock contention, plan regression, N+1 or full scan.
- **code-review**: injection risk, implicit cast, non-sargable predicate, unbounded result set.
- **refactoring**: view/CTE extraction, migration expand-contract, result-shape compatibility.
- **testing**: migration validation, isolation-level tests, deterministic seed data.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Query correctness and shape | New or changed SELECT/UPDATE/DELETE, report query, ORM builder, aggregation, join, filter, or sort. | Preserve result semantics, cardinality, tenant/object predicates, NULL handling, and bounded result size. | SQL/ORM call site, parameters, expected rows, fixtures, and plan or not-verified disclosure. | `relational-database`, `repository-persistence`, `quality-test-gate` | Syntax tutoring or style-only formatting. |
| Injection and dynamic SQL | Raw SQL, string interpolation, identifier interpolation, user-controlled filter/sort, or report builder. | Separate values from identifiers and keep allowlists, parameter binding, and output redaction explicit. | Parameter binding proof, identifier allowlist, malicious-input test, same-pattern scan. | `security-privacy-gate`, `input-validation`, `data-api-contract-changer` | Trusting ORM use without inspecting generated SQL. |
| Transaction, lock, and isolation | Write transaction, upsert, batch update, queue worker, retry, `FOR UPDATE`, gap lock, or deadlock report. | Bound lock duration, isolation anomalies, retry behavior, rollback, and idempotency. | Transaction map, isolation level, lock analysis, concurrency test or residual owner. | `transaction-consistency`, `data-middleware-change-builder` | Sequential unit tests as concurrency proof. |
| Migration and schema compatibility | Column/index/table/constraint/default change, backfill, enum change, online DDL, or rollback concern. | Stage expand/migrate/contract without old/new code breakage or hot-table outage. | Migration phases, row count, lock class, forward/rollback command, validation query. | `data-migration-design`, `delivery-release-gate`, `quality-test-gate` | Direct rename/drop without caller search. |
| Existing SQL evidence reuse | Repository graph, project memory, old report, generated query, telemetry, or prior validation says safe/fast. | Confirm current source, schema, indexes, statistics, migrations, consumers, and validation freshness. | Inspected paths, accepted/rejected memory, command exit code, artifact/report path, evidence limits. | `repository-graph-analysis`, `project-memory-governance`, `validation-broker` | Stale memory or dev-data timing as closure proof. |

# Non-Negotiable Rules

- **Parameterized queries always.** No string concatenation of user input (or any input) into SQL. Use driver-native parameters (`$1` Postgres, `?` MySQL, named params), prepared statements, or query-builder macros (sqlx, Diesel, jOOQ).
- **`EXPLAIN ANALYZE` on every non-trivial query** before merge. "Non-trivial" = joins, aggregations, subqueries, or filters on tables > 100k rows. Plan attached to PR.
- **Indexes match query patterns and have a write-cost budget.** Each new index documents: queries it supports (with `EXPLAIN`), estimated write-cost increase, partial-index opportunity (`WHERE active=true`), composite-column-order rationale (most-selective-leftmost or query-ordering match).
- **Pagination is stable and bounded.** Offset pagination is forbidden for large datasets (`OFFSET 100000` scans 100k rows). Use **keyset / cursor pagination** (`WHERE (sort_col, id) > (?, ?) ORDER BY sort_col, id LIMIT N`).
- **NULL semantics explicit.** `col = NULL` never matches — use `IS NULL`. `NOT IN (subquery)` is broken when subquery returns NULL — use `NOT EXISTS`. Aggregates ignore NULL (`COUNT(col)` vs `COUNT(*)`).
- **Timezone-aware timestamps**: Postgres `TIMESTAMPTZ` (not `TIMESTAMP`); MySQL `TIMESTAMP` (stores UTC) or explicit timezone handling at app boundary. Never store local-time without timezone metadata.
- **Money / precise decimals**: `NUMERIC(p, s)` / `DECIMAL(p, s)`. Never `FLOAT` / `DOUBLE` / `REAL` for currency.
- **Migrations are expand-contract** for any change visible to the running application: add new column / index / table (expand) → deploy code that writes both / reads new → backfill → deploy code that only reads new → drop old (contract). No simultaneous code+schema breaking change.
- **Locking discipline on production tables**: `ALTER TABLE` on a large MySQL InnoDB table without `ALGORITHM=INPLACE, LOCK=NONE` (or online-schema-change tool) is rejected. Postgres `CREATE INDEX CONCURRENTLY` for any index on a non-trivial table.
- **No unbounded scans on user-facing paths.** Every user-facing query has `LIMIT` (with bound check) or `EXPLAIN` shows index access; sequential scan on > 100k rows for a user-facing query is rejected.
- **Migration is forward + rollback testable**, executed in CI against a real engine (Testcontainers or equivalent) before merge.

# Industry Benchmarks

- **PostgreSQL documentation**, **PostgreSQL Internals** (Egor Rogov), **MySQL Reference Manual**, and **High Performance MySQL, 4th ed.** (Schwartz / Tkachenko / Zaitsev).
- **SQL Performance Explained** (Markus Winand) — the canonical reference for indexes and pagination across engines.
- **OWASP A03:2021 Injection** — parameterized-query mandate; **SQL Injection Prevention Cheat Sheet**.
- **Postgres lock matrix**, MySQL InnoDB gap / next-key locks, and ACID isolation-level documentation.
- **`gh-ost` / `pt-online-schema-change` / `pg_repack`** documentation for online migrations.
- **`auto_explain`, `slow_query_log`, `pg_stat_statements`, `performance_schema`, and Use The Index, Luke** for production query observability and indexing practice.

# Selection Rules

Select when SQL, migrations, reports, analytics, query performance, locking, pagination, injection, NULL behavior, timezone, or money correctness appear. Pair with `data-middleware-change-builder`, `data-migration-design`, `transaction-consistency`, `indexing-query-optimization`, `security-privacy-gate`.

# Proactive Professional Triggers

- **Signal:** SQL text is composed from request input, report filters, sort fields, table names, or tenant/resource IDs. **Hidden risk:** injection, IDOR, tenant leakage, or plan instability can survive happy-path tests. **Required professional action:** require parameter binding for values, allowlists for identifiers, caller-derived identity, and a same-pattern scan. **Route to:** `security-privacy-gate`, `input-validation`, `permission-boundary-modeling`. **Evidence required:** malicious-input or denied-case test output, parameterization proof, inspected call sites, and residual exception owner.
- **Signal:** a query adds joins, aggregations, windows, `DISTINCT`, pagination, soft-delete filters, or tenant predicates. **Hidden risk:** duplicate/missing rows, N+1 fan-out, unstable cursors, or cross-tenant results appear only at realistic cardinality. **Required professional action:** inspect current SQL/ORM source, expected row shape, fixtures, and representative plan before accepting the query. **Route to:** `relational-database`, `indexing-query-optimization`, `quality-test-gate`. **Evidence required:** query text, cardinality assumption, `EXPLAIN`/plan artifact, boundary-row test, and not-verified data-volume limits.
- **Signal:** write path changes transaction scope, isolation level, upsert, batch update, retry, lock statement, or queue worker SQL. **Hidden risk:** lost updates, deadlocks, gap locks, duplicate side effects, or partial rollback are invisible in sequential tests. **Required professional action:** map transaction boundaries, lock order, retry/idempotency behavior, and concurrency validation depth. **Route to:** `transaction-consistency`, `data-middleware-change-builder`, `quality-test-gate`. **Evidence required:** isolation/lock analysis, concurrent test or dry-run command, exit code, and unresolved scheduler risk.
- **Signal:** migration changes a column, index, constraint, default, enum, partition, backfill, or drop/rename path. **Hidden risk:** old/new code incompatibility, hot-table locks, replica lag, partial backfill, or irreversible rollback. **Required professional action:** require expand/migrate/contract phases, caller search, rollback tier, validation query, and release sequencing. **Route to:** `data-migration-design`, `delivery-release-gate`, `data-api-contract-changer`. **Evidence required:** row-count estimate, lock class, forward/rollback command, validation report, and consumer compatibility note.
- **Signal:** repository graph, project memory, generated SQL, old slow-query report, or prior execution claims the SQL path is safe, unused, indexed, or tested. **Hidden risk:** stale schema, changed migration ledger, missing report consumer, outdated stats, or final edit after validation invalidates the claim. **Required professional action:** confirm current source, migrations, generated artifacts, telemetry, and validation freshness before closure. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** inspected paths, accepted/rejected memory, fresh command output or artifact path, evidence limits, and residual owner.

# Risk Escalation Rules

- Escalate to `data-middleware-change-builder` for the broader implementation (repository, ORM, query-builder layer).
- Escalate to `data-migration-design` for schema migration planning, expand-contract sequencing, backfill strategy.
- Escalate to `transaction-consistency` for isolation level, lock duration, two-phase, deadlock risk.
- Escalate to `indexing-query-optimization` for deep plan analysis, partial indexes, BRIN/GIN/GIST selection, denormalization decisions.
- Escalate to `security-privacy-gate` for injection risk, sensitive-data exposure, RLS / column encryption / audit-log requirements.
- Escalate to `reliability-observability-gate` for production query-latency SLO impact.

# Critical Details

- **`OFFSET` pagination is O(offset)** — a query with `OFFSET 100000 LIMIT 20` reads and discards 100k rows even with a perfect index. Keyset pagination is O(log n) per page. The cost difference at scale is 1000× or more.
- **`SELECT *`** in production code defeats projection pushdown and breaks when the schema evolves. List columns explicitly.
- **N+1 query** — fetching parent rows then issuing one query per parent for children. Fix via `JOIN`, `IN` batching, or DataLoader pattern.
- **Index column order**: composite index `(a, b, c)` can serve `WHERE a=?`, `WHERE a=? AND b=?`, `WHERE a=? AND b=? AND c=?` — not `WHERE b=?` or `WHERE c=?`. Order matters.
- **Index covering**: include all columns the query needs (Postgres `INCLUDE`, MySQL covering composite) to enable index-only scan and avoid heap lookups.
- **Partial indexes**: `CREATE INDEX ... WHERE active = true` for queries that always filter on `active=true` — smaller index, faster, less write cost.
- **Implicit type coercion defeats index**: `WHERE varchar_col = 123` (integer literal) may force a scan in MySQL because of charset / collation conversion. Match types.
- **`NOT IN` + NULL** — if the subquery returns even one NULL, `NOT IN` returns no rows. Use `NOT EXISTS` instead.
- **Locking**: long-running `UPDATE` / `DELETE` on a busy table blocks readers (depending on isolation). Batch via `WHERE id BETWEEN ? AND ? LIMIT N` chunks; release & reacquire row locks between chunks.
- **MySQL InnoDB gap / next-key locks**: a range query in `REPEATABLE READ` locks gaps to prevent phantoms, causing surprising deadlocks; use `READ COMMITTED` where this is intolerable (with the trade-off of phantom reads).
- **Postgres `VACUUM` / dead tuples**: heavy updates without `HOT update` accumulate dead tuples; `autovacuum` settings tuned for write-heavy tables; bloat measured via `pgstattuple`.
- **`CREATE INDEX CONCURRENTLY` (Postgres)** does not block writes but is slower and can fail — verify state after; build in a separate transaction.
- **MySQL `ALTER TABLE` online**: `ALGORITHM=INPLACE, LOCK=NONE` works for many cases (since 5.6+); fall back to `gh-ost` / `pt-osc` when it doesn't.
- **Timezone**: store UTC in DB; convert at presentation layer to user/tenant timezone. `TIMESTAMPTZ` (Postgres) stores UTC internally and converts on read based on session timezone.
- **Migration with default value on huge table**: in older Postgres (< 11) and MySQL pre-instant-DDL, adding a column with `DEFAULT` rewrites the table. In Postgres 11+ and MySQL 8.0.12+, default values are stored in metadata (instant-add); verify version + use of `DEFAULT` constant (not volatile expression).

# Failure Modes

- **SQL injection** — Symptom: attacker controls query. Cause: string concatenation. Detection: lint (semgrep / CodeQL); driver review. Impact: data breach.
- **OFFSET pagination cliff** — Symptom: page latency grows with page number. Cause: `OFFSET N LIMIT M`. Detection: load test deep pagination; plan review. Impact: timeout on deep pages.
- **Sequential scan on large table** — Symptom: query is fast on dev (10k rows), slow on prod (10M rows). Cause: missing or unusable index. Detection: `EXPLAIN ANALYZE` against prod-shape data. Impact: latency cliff at scale.
- **N+1 query** — Symptom: page load triggers 100s of DB queries. Cause: per-row child fetch in loop. Detection: query-log + APM trace. Impact: latency, DB load.
- **Migration lock-out** — Symptom: production `ALTER TABLE` blocks readers/writers for minutes. Cause: not using online-schema-change. Detection: dry-run on prod-size replica. Impact: outage during migration window.
- **NULL in `NOT IN`** — Symptom: query returns empty set unexpectedly. Cause: NULL in subquery. Detection: review + test with NULL fixtures. Impact: data missing from reports.
- **`FLOAT` for money** — Symptom: penny rounding drift; reconciliation fails. Cause: float type. Detection: schema review. Impact: financial discrepancy.
- **Timezone confusion** — Symptom: events appear at wrong time; cron runs at DST shift; calendars off. Cause: `TIMESTAMP` without TZ; local-time stored. Detection: schema + app-layer audit. Impact: scheduling bugs, audit / compliance issues.
- **`SELECT *` brittleness** — Symptom: app breaks after schema add. Cause: positional column expectation. Detection: lint / review. Impact: deploy break.
- **Pre-Postgres-11 `ADD COLUMN ... DEFAULT`** — Symptom: migration locks table for minutes. Cause: default value rewrites table. Detection: version + DEFAULT-constant check. Impact: outage.
- **MySQL `REPEATABLE READ` next-key deadlock** — Symptom: deadlock between range update and insert. Cause: gap lock. Detection: deadlock log; isolation review. Impact: failed transactions, retry storms.

# Reference Loading Policy

Load [references/checklist.md](references/checklist.md) when SQL changes touch dynamic queries, parameterization, joins, indexes, query plans, transactions/isolation, migrations, backfills, tenant predicates, or data safety. Use [examples/example-output.md](examples/example-output.md) when the required review shape is unclear. Do not load references for a trivial static lookup query with no user input or data-shape impact.

# Output Contract

Return a **SQL Usage Review** containing:
- **Mode selected**: query correctness, injection/dynamic SQL, transaction/lock/isolation, migration/schema compatibility, or existing-evidence reuse, with trigger signal
- **Boundaries inspected**: SQL/ORM call sites, schema/migrations, indexes, tests/fixtures, tenant/object filters, report/API consumers, generated SQL, telemetry, and skipped boundaries with reason
- **Engine** (Postgres / MySQL / SQLite / etc.) and version
- **Query purpose** + parameters
- **`EXPLAIN ANALYZE` plan** attached (with `BUFFERS` where Postgres); index usage verified
- **Indexes**: each new / changed index with supported queries, write-cost estimate, composite-order rationale
- **Lock + transaction behavior**: isolation level; row / range / table locks; long-run risk
- **Pagination**: keyset / cursor (preferred) or bounded offset with justification
- **NULL handling**: each predicate / aggregate / `NOT IN` audited
- **Timezone**: `TIMESTAMPTZ` (Postgres) or UTC-storage discipline (MySQL)
- **Numeric precision**: `NUMERIC` / `DECIMAL` for money
- **Migration plan**: forward + rollback; online-schema-change tool if applicable; expand-contract sequence; lock-impact dry-run on prod-size replica
- **Injection safety**: parameterization at every input site
- **Connection pool**: size calculated via Little's Law
- **Tests**: query unit tests against real engine (Testcontainers); migration forward+rollback test; perf assertion on critical queries
- **SQL graph, memory, and execution freshness**: repository graph, project memory, generated SQL, prior reports, telemetry, and validation runs accepted, rejected, stale, or not verified after final edit
- **SQL validation proof**: literal command, exit code, artifact/report path, and what the output proves or does not prove
- **Tool permission boundary**: query-plan, migration, lint, test, shell, connector, or generated-artifact command class; sandbox/approval state; write scope; and secret-output redaction rule
- **Accepted SQL deviations** with owner, scope, expiration, and cleanup trigger

# Evidence Contract

A SQL change is professionally complete only when the output includes:

- **Parameterization**: no string-concatenated SQL or unsafe interpolation.
- **Query shape**: joins, filters, grouping, sorting, pagination, and expected cardinality.
- **Index and plan evidence**: index selection, EXPLAIN/ANALYZE, selectivity, scan type, and write overhead.
- **Transaction/isolation**: locking, isolation level, deadlock risk, retry behavior, and rollback.
- **Migration/data safety**: nullable/default/backfill strategy, constraint validation, and compatibility phase.
- **Validation evidence**: query plan, migration dry run, integration test, or not-verified disclosure.
- **What evidence proves**: the inspected SQL path is parameterized, planned, and safe for the declared data shape.
- **What evidence does not prove**: production cardinality, lock contention, replica lag, or untested tenants.
- **Graph and memory freshness**: current source, schema, migrations, generated SQL, telemetry, prior reports, and execution claims confirmed or rejected before closure.
- **Residual risk**: untested data path, owner, and next gate.

# Quality Gate

1. Every query parameterized; no string-concat of input.
2. `EXPLAIN ANALYZE` plan attached for every non-trivial query; index usage verified.
3. New indexes documented with supported queries + write-cost estimate.
4. Pagination is keyset / cursor, or bounded offset ≤ 1000 with justification.
5. NULL semantics audited (`IS NULL` / `NOT EXISTS`).
6. `TIMESTAMPTZ` (Postgres) or UTC discipline; no money in `FLOAT`.
7. Migration is expand-contract for any app-visible change; online-schema-change tool used for large tables; lock impact dry-run on prod-size replica.
8. Migration tested forward + rollback in CI against real engine.
9. Connection pool sized via Little's Law.
10. sqlfluff (or equivalent) lint green; query covered by test against real engine.
11. Validation report maps each changed SQL/query/migration path to command, exit code, covered risk, stale/not-run target, and residual owner.
12. Tool permission/sandbox record exists for query-plan, migration, lint, test, shell, connector, or artifact-writing commands.

# Used By

data-middleware-change-builder, data-api-contract-changer, backend-change-builder, quality-test-gate, reliability-observability-gate

# Handoff

- **`data-migration-design`** for schema migration planning and backfill.
- **`transaction-consistency`** for isolation, lock duration, deadlock risk.
- **`indexing-query-optimization`** for deep plan analysis, advanced index strategies (BRIN / GIN / GIST / hash / partial / covering).
- **`security-privacy-gate`** for injection, RLS, sensitive-data exposure, audit-log.
- **`reliability-observability-gate`** for production query-latency SLO impact.

# Completion Criteria

Review is complete when: queries are parameterized; non-trivial queries have `EXPLAIN ANALYZE` plans attached; indexes are justified with cost estimates; pagination is keyset-based; NULL / timezone / numeric semantics are explicit; migrations are expand-contract and tested forward + rollback; lock impact has been verified on prod-shape data; graph/memory/execution claims are current-source confirmed; tool permissions are recorded; and any exception is documented with owner, scope, expiration.
