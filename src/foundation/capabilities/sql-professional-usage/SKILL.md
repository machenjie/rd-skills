---
name: sql-professional-usage
description: Use when writing or reviewing SQL for application queries, migrations, reports, or analytics with focus on transaction safety, indexing, query plans, locks, pagination, null semantics, timezones, data correctness, injection safety, and migration compatibility.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "96"
changeforge_version: 0.1.0
---

# Mission

Enforce professional SQL usage for application queries, migrations, reports, and analytics: parameterized queries, plan-verified indexes, bounded and stable pagination, explicit NULL / timezone / numeric-precision semantics, lock-aware migrations, and expand-contract delivery. Reject string-composed queries, plan-unverified "it works locally" changes, and migrations that hold long locks on production tables.

# Pinned Engine / Tooling Baseline (SQL)

- **Postgres**: ≥ 16 (17 GA Sep 2024); 15 acceptable through its support window. 13 and below approach EOL — plan upgrade. Use `psql --no-psqlrc`, `EXPLAIN (ANALYZE, BUFFERS, VERBOSE)`, `pg_stat_statements`, `auto_explain`.
- **MySQL**: ≥ 8.4 LTS (or 8.0 through its EOL April 2026). 5.7 is EOL — forbidden for new work. Use `EXPLAIN ANALYZE` (8.0.18+), `performance_schema`, `sys` schema.
- **SQLite**: ≥ 3.45 for new use cases; `PRAGMA foreign_keys=ON`, WAL mode, busy-timeout configured.
- **Linter / formatter**: `sqlfluff` ≥ 3 with dialect set; `pgFormatter` (Postgres); CI runs lint.
- **Migration tools**: `Flyway` ≥ 10 / `Liquibase` ≥ 4.27 / `Atlas` / `golang-migrate` / `Alembic` (Python) / `Prisma Migrate` / `Rails ActiveRecord`. Migrations versioned, idempotent, and **reviewed**.
- **Online schema change (large tables)**: `gh-ost` or `pt-online-schema-change` (MySQL); `pg_repack` (Postgres) for table rewrites; concurrent index builds (`CREATE INDEX CONCURRENTLY` in Postgres, `ALTER TABLE ... ALGORITHM=INPLACE, LOCK=NONE` in MySQL 8).
- **Query observability**: `pg_stat_statements` + `auto_explain.log_min_duration` (Postgres); `slow_query_log` + `performance_schema.events_statements_summary_by_digest` (MySQL).
- **Drivers (application side)**: parameterized-query-mandatory drivers (`psycopg` v3 / `asyncpg` for Postgres-Python; `pgx` for Go; `sqlx` for Rust; `node-postgres` for Node; `jdbc` with `PreparedStatement` for JVM).
- **Connection pool**: per-pool size calculated via Little's Law (peak QPS × query latency × safety factor 1.5–2); never unbounded.

# When To Use

Use when SQL queries, migrations, reports, analytics, indexes, transaction behavior, lock behavior, pagination, or database-backed correctness change. Use whenever an `EXPLAIN` plan is needed; whenever a migration touches a table with > 1M rows; whenever a query joins > 2 tables or filters/sorts on un-indexed columns.

# Do Not Use When

Do not use as a syntax lesson. Do not use to bypass `data-migration-design` (schema-evolution planning) or `transaction-consistency` (isolation / two-phase) when the change is structurally about those.

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

- **PostgreSQL documentation** (`postgresql.org/docs/current/`) and **"PostgreSQL Internals"** (Egor Rogov).
- **MySQL 8.0 Reference Manual** + **High Performance MySQL, 4th ed.** (Schwartz / Tkachenko / Zaitsev).
- **SQL Performance Explained** (Markus Winand) — the canonical reference for indexes and pagination across engines.
- **OWASP A03:2021 Injection** — parameterized-query mandate; **SQL Injection Prevention Cheat Sheet**.
- **Postgres lock matrix** and MySQL InnoDB lock behavior (gap / next-key locks).
- **ACID + isolation levels** (Postgres: Read Committed default, Serializable available; MySQL InnoDB: Repeatable Read default).
- **`gh-ost` / `pt-online-schema-change` / `pg_repack`** documentation for online migrations.
- **`auto_explain` (Postgres) / `slow_query_log` (MySQL)** + **`pg_stat_statements` / `performance_schema`** for production query observability.
- **EVAN P / Brent Ozar / Use The Index, Luke** as canonical educational references.

# Selection Rules

Select when SQL, migrations, reports, analytics, query performance, locking, pagination, injection, NULL behavior, timezone, or money correctness appear. Pair with `data-middleware-change-builder`, `data-migration-design`, `transaction-consistency`, `indexing-query-optimization`, `security-privacy-gate`.

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
- **`COUNT(*)` over a large table** is expensive in Postgres (MVCC requires scanning all visible rows). Use `pg_class.reltuples` estimate or maintain a counter for cheap counts; MySQL InnoDB count is also full-table-scan since 5.7+.
- **`CREATE INDEX CONCURRENTLY` (Postgres)** does not block writes but is slower and can fail — verify state after; build in a separate transaction.
- **MySQL `ALTER TABLE` online**: `ALGORITHM=INPLACE, LOCK=NONE` works for many cases (since 5.6+); fall back to `gh-ost` / `pt-osc` when it doesn't.
- **Connection-pool starvation**: too-low pool causes latency; too-high pool causes DB-side context-switch / lock contention. Little's Law: `pool_size ≈ peak_qps × avg_query_latency × 1.5–2`.
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
- **Connection pool exhaustion** — Symptom: app times out waiting for connection; DB has idle slots. Cause: pool sized too small or long-held connection. Detection: pool-wait metric + Little's Law. Impact: cascading failure.
- **Pre-Postgres-11 `ADD COLUMN ... DEFAULT`** — Symptom: migration locks table for minutes. Cause: default value rewrites table. Detection: version + DEFAULT-constant check. Impact: outage.
- **MySQL `REPEATABLE READ` next-key deadlock** — Symptom: deadlock between range update and insert. Cause: gap lock. Detection: deadlock log; isolation review. Impact: failed transactions, retry storms.

# Output Contract

Return a **SQL Usage Review** containing:
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
- **Accepted exceptions** with owner / scope / expiration

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

# Used By

data-middleware-change-builder, data-api-contract-changer, backend-change-builder, quality-test-gate, reliability-observability-gate

# Handoff

- **`data-migration-design`** for schema migration planning and backfill.
- **`transaction-consistency`** for isolation, lock duration, deadlock risk.
- **`indexing-query-optimization`** for deep plan analysis, advanced index strategies (BRIN / GIN / GIST / hash / partial / covering).
- **`security-privacy-gate`** for injection, RLS, sensitive-data exposure, audit-log.
- **`reliability-observability-gate`** for production query-latency SLO impact.

# Completion Criteria

Review is complete when: queries are parameterized; non-trivial queries have `EXPLAIN ANALYZE` plans attached; indexes are justified with cost estimates; pagination is keyset-based; NULL / timezone / numeric semantics are explicit; migrations are expand-contract and tested forward + rollback; lock impact has been verified on prod-shape data; connection pool is Little's-Law-sized; and any exception is documented with owner, scope, expiration.
