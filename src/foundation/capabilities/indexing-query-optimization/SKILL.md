---
name: indexing-query-optimization
description: Designs indexes and query changes from predicates, sorting, cardinality, plans, and write cost instead of blind index addition.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "47"
changeforge_version: 0.1.0
---

# Mission

Optimize query execution paths by matching index design to **real query predicates, sort order, cardinality, access frequency, and write cost** — rejecting blind index addition, treating execution plan evidence as mandatory rather than optional, and accounting for production migration risk before any change is merged.

# When To Use

Use this capability when a change: adds or modifies database indexes; introduces new query filters, joins, or sort clauses; changes ORM query patterns (N+1 risk, eager vs lazy loading); adds pagination to queries; introduces reporting or analytics queries against operational tables; modifies table schema in ways that affect existing indexes; or investigates a slow-query alert or latency regression on a data access path.

# Do Not Use When

Do not use this capability for non-relational data store optimization (use `nosql-database` for DynamoDB/MongoDB partition and index design). Do not use it for full-text search optimization (use `search-analytics-design` for Elasticsearch/Solr relevance tuning). Do not add indexes "just in case" — every index has a write amplification cost, a storage cost, and a maintenance burden; justification is mandatory. Boundary: repository graph, project memory, execution trajectory, and old validation reports are path selectors, not trusted production proof; current source, schema, plan, telemetry, owner, and ownership evidence must close the claim. This capability does not own permission, tenant, or API contract semantics except where those predicates change query shape; route those boundaries to the owning capability.

# Stage Fit

Owns query/index optimization during data-middleware planning, coding, debugging, bug-fix repair, code-review, refactoring, testing, release readiness, and handoff when the primary risk is a concrete SQL/ORM read path, execution plan, pagination strategy, or physical index lifecycle. In planning, it turns current query evidence into index/query/pagination decisions and migration-safe validation obligations. During coding and review, it rejects blind index additions, dev-data-only plans, N+1 misdiagnosis, unsafe offset pagination, or build/drop decisions without write-cost and rollback evidence. Repository graph, project memory, and execution trajectory may point to slow queries or prior fixes, but current SQL/ORM call sites, schema/index definitions, telemetry, and execution plans must confirm the optimization target before the output treats that evidence as authoritative.

# Non-Negotiable Rules

- **Every index must be tied to a named query.** Index justification format: "Index `idx_orders_user_status` exists to serve query: `SELECT ... FROM orders WHERE user_id = $1 AND status = $2 ORDER BY created_at DESC LIMIT 50`." No index without a named beneficiary query.
- **Execution plan is required before and after.** Use `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` (PostgreSQL), `EXPLAIN ANALYZE` (MySQL), or equivalent. Confirm: Seq Scan changed to Index Scan; rows actually scanned match expected selectivity; buffer hits indicate cache usage. Plan estimates on empty/dev tables are misleading — test on production-scale data or realistic data volumes.
- **Composite index column order: most selective first, then equality predicates, then range predicates, then sort column.** For `WHERE status = $1 AND user_id = $2 ORDER BY created_at DESC`: index column order = `(user_id, status, created_at DESC)` — equality predicates first, matching the sort last. A mismatch in column order causes the index to be skipped entirely for sorting and requires a filesort.
- **Write amplification is calculated, not ignored.** For every proposed index on a high-write table: estimate write overhead = (rows written per second) × (index maintenance cost per row per index). A table receiving 5,000 INSERT/s with 5 indexes has meaningful write amplification. If index count is causing write latency SLA risk, the access pattern must be reconsidered.
- **Online index builds for tables > 1 million rows.** PostgreSQL: `CREATE INDEX CONCURRENTLY` — does not hold a lock; takes longer; may fail and leave an invalid index. MySQL: `ALTER TABLE ... ALGORITHM=INPLACE, LOCK=NONE`. Never use `CREATE INDEX` (blocking) on a live production table with significant traffic without confirming the lock duration is acceptable.
- **Offset pagination is forbidden for tables > 100,000 rows without a keyset/cursor alternative.** `OFFSET 10000 LIMIT 20` scans and discards 10,000 rows before returning 20. For large tables this becomes O(N) with N proportional to page depth. Use keyset pagination: `WHERE (created_at, id) < ($last_created_at, $last_id) ORDER BY created_at DESC, id DESC LIMIT 20`.
- **Covering index optimization requires column order discipline.** A covering index that includes all SELECT columns avoids a table heap fetch entirely. Column order: filter columns (equality) → sort columns → include columns (SELECT targets). PostgreSQL supports `INCLUDE` clause for non-key include columns (PostgreSQL 11+) to avoid key bloat.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Slow-query diagnosis | Slow query alert, latency regression, high scan cost, or profiling confirms database query as bottleneck. | Identify the exact query, plan bottleneck, cardinality/selectivity issue, and non-index causes before proposing a fix. | Current SQL/ORM call site, telemetry or trace, representative `EXPLAIN`, data volume, and baseline latency. | `profiling`, `observability`, `performance-budgeting` | Adding an index from intuition or dev-data timing. |
| New or changed read path | Feature adds filters, joins, sorting, grouping, reporting query, or repository method. | Design query and index together so access pattern, result size, and sort order are explicit before merge. | Query text/ORM builder, predicates, sort, pagination, expected cardinality, write rate, and existing indexes. | `repository-persistence`, `data-model-design`, `relational-database` | Treating ORM-generated SQL as unknown. |
| Index lifecycle change | Add, drop, rebuild, partial/functional/covering index, or index migration on hot table. | Tie each index to a beneficiary query and manage build, rollback, write cost, and post-deploy usage. | Named query, before/after plan, build strategy, lock risk, write amplification, and `idx_scan`/usage monitoring. | `data-migration-design`, `release-rollback`, `quality-test-gate` | Blocking builds or drops without usage evidence. |
| Pagination and ordering correction | Offset pagination, unstable sorting, deep pages, API cursor, infinite scroll, or timeout at page depth. | Select keyset/cursor/deferred join strategy and matching composite index. | Order columns, tie-breaker, cursor semantics, table size, depth behavior, and compatibility limits. | `api-contract-design`, `frontend-api-integration` | Offset on large tables without disclosure. |
| Write-heavy production tradeoff | High insert/update rate, many existing indexes, hot partitions, or query benefit competes with write SLO. | Balance read improvement against write amplification, storage, vacuum/maintenance, and rollback. | Write rate, index count, storage growth, vacuum/maintenance impact, read frequency, and SLO budget. | `performance-budgeting`, `reliability-observability-gate` | Read-only optimization claims on write paths. |

# Industry Benchmarks

Anchor against PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)`, `pg_stat_statements`, and `pg_stat_user_indexes`; MySQL `EXPLAIN FORMAT=JSON`; Use The Index, Luke; Markus Winand's SQL Performance Explained; Kleppmann's storage-engine tradeoffs; Percona slow-query analysis; and production-safe online index-build practices. Keep this body focused on selection and evidence rules; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed index-type selection, plan-reading signals, pagination comparisons, and benchmark examples.

# Selection Rules

Select this capability when **query performance, index design, or execution plan analysis** are the primary concern. Adjacent routing:

- Prefer `data-model-design` when the primary concern is schema design, normalization, and relationship modeling.
- Prefer `data-migration-design` when the primary concern is the migration process for adding the index (online build, rollback, gh-ost/pt-osc).
- Prefer `nosql-database` when the primary concern is non-relational data store partition key and secondary index selection.
- Prefer `search-analytics-design` when the primary concern is full-text search relevance, faceted search, or OLAP queries.
- Prefer `reliability-observability-gate` for production slow query alerting and SLO impact review.

# Risk Escalation Rules

Escalate when: an index build is planned on a table > 10 million rows in production (estimate build time and lock duration); a query modification affects a billing, financial reporting, or audit table; an index is being dropped that might be used by undocumented queries; the table is write-heavy (> 1,000 writes/s) and additional index maintenance cost could cause write latency SLA breach; a query plan regression is detected in production (latency P99 increase correlated with a schema change).

# Proactive Professional Triggers

- **Signal:** An index is proposed without a named query, current plan, or usage metric. **Hidden risk:** the index becomes permanent write/storage cost with no measurable read benefit. **Required professional action:** name the beneficiary query, capture current plan, and reject or defer until evidence exists. **Route to:** `indexing-query-optimization`, `quality-test-gate`. **Evidence required:** query text, plan, selectivity, and expected benefit.
- **Signal:** A query plan is based on dev data, empty tables, stale project memory, repository graph proximity, or prior agent trajectory. **Hidden risk:** stale or unrepresentative evidence hides production full scans, bad join order, or unused indexes. **Required professional action:** confirm with current source, schema, statistics, and representative data or disclose not-verified limits. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, data-volume freshness, telemetry/plan source, and evidence limits.
- **Signal:** N+1 ORM behavior is described as a missing-index problem. **Hidden risk:** faster individual queries still produce request-level latency from query fan-out. **Required professional action:** count per-request queries and decide between eager loading, batching, query rewrite, or index. **Route to:** `repository-persistence`, `profiling`. **Evidence required:** query-count trace, ORM call site, selected repair, and residual index need.
- **Signal:** Pagination uses `OFFSET` or sorting without a stable tie-breaker on a large table. **Hidden risk:** deep-page latency, duplicate/missing rows under concurrent inserts, and unstable API cursors. **Required professional action:** evaluate keyset/cursor/deferred join and matching composite index. **Route to:** `api-contract-design`, `frontend-api-integration` when API/UI semantics are affected. **Evidence required:** table size, sort columns, cursor contract, and compatibility tradeoff.
- **Signal:** Index build, rebuild, or drop touches a large, write-heavy, regulated, audit, or revenue table. **Hidden risk:** lock outage, write latency regression, compliance/reporting regression, or irreversible rollback gap. **Required professional action:** route migration/release planning and monitoring before approval. **Route to:** `data-migration-design`, `delivery-release-gate`, `reliability-observability-gate`. **Evidence required:** online build/drop plan, rollback path, usage monitoring, and write-cost estimate.

# Critical Details

Execution plan estimates on development data diverge significantly from production at scale. Precision failures:

- **Index column order mismatch.** Index: `(status, user_id, created_at)`. Query: `WHERE user_id = $1 AND status = $2 ORDER BY created_at DESC`. PostgreSQL may not use this index for sorting because the leading column `status` has low cardinality (only 3 values) and the planner estimates a partial index scan would be more expensive than a filesort. Correct order: `(user_id, status, created_at DESC)`.
- **Low-cardinality leading column.** A table has `gender` column with values {M, F, X} (3 values; cardinality = 3; each value covers ~33% of rows). An index with `gender` as the leading column will not be selective enough for the planner to use — a sequential scan of 33% of the table is often faster than an index scan + heap fetch. Low-cardinality columns belong after selective columns in composite indexes.
- **Unused indexes on write-heavy table.** A table receives 10,000 inserts/sec. It has 8 indexes that were added incrementally over 2 years. Query pg_stat_user_indexes: 3 of them have `idx_scan = 0` for 30 days. Those 3 indexes are consuming write capacity and disk space with no read benefit. Remove unused indexes on write-heavy tables.
- **N+1 ORM query.** An ORM loads 100 orders. Then for each order, it loads `order.customer.name` — executing 100 additional SELECT statements. Total: 101 queries. This is not an index problem; it is an eager loading problem. Fix with `JOIN FETCH` or `include: ['customer']` in the ORM query. No index can fix N+1.
- **Statistics staleness.** After a bulk import of 5 million rows, PostgreSQL statistics are stale. The planner estimates 1,000 rows but scans 5 million. Run `ANALYZE orders;` after bulk imports. Schedule `autovacuum` appropriately for high-churn tables.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 query/index selection and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete optimization plan, when plan evidence or write-cost coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when index-type choice, plan-reading detail, pagination tradeoffs, or benchmark examples are needed. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on project memory, repository graph, execution trajectory, validation freshness, tool permission boundaries, or a changed-query-to-validation map. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load these references for pure routing or trivial wording work where the output contract and quality gate are enough.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Index added without named query | Cannot verify if index is used; cannot measure benefit; cannot justify maintenance cost |
| `CREATE INDEX` (blocking) on production table | Table locked for minutes; production outage |
| Low-cardinality leading column | Planner skips index; sequential scan 10x slower |
| `OFFSET 50000 LIMIT 20` on 10M row table | 50,000 row scan per page; P99 latency 5+ seconds at deep pages |
| N+1 ORM queries "fixed" by indexing | 100 queries become 100 fast queries; root cause unaddressed |
| Index on every column "for safety" | Write amplification; INSERT latency degraded; storage doubled |
| Plan only on dev data (100 rows) | Seq scan on 100 rows = fast; same Seq scan on 10M rows = slow |
| Dropping index without pg_stat_user_indexes check | Accidentally removes actively-used index; production regression |

# Failure Modes

- **Wrong column order:** index added in wrong column order; planner falls back to sequential scan; query 100x slower than expected; detected only in production load test.
- **Blocking build:** blocking `CREATE INDEX` on orders table; table locked for 8 minutes; all checkout requests timeout; P0 incident.
- **Deep offset pagination:** `OFFSET` pagination on audit log table (50M rows); user navigates to page 2,500; query scans 50,000 rows; timeout; CSAT impact.
- **N+1 misdiagnosis:** ORM query on customer dashboard loads 200 customers plus 200 individual account queries; dashboard latency 8s; misdiagnosed as missing index; eager loading root cause unaddressed.
- **Write-heavy unused index:** unused index on write-heavy table; 6 unused indexes on `events` table; INSERT latency increased from 2ms to 12ms; discovered during load test.
- **Stale statistics:** statistics staleness after bulk import; planner chooses wrong join order; reporting query 30x slower than expected; `ANALYZE` not run post-import.
- **Low-cardinality leading column:** index on `status` column where status = 'active' matches 80% of rows; planner uses sequential scan; index never used; write cost paid with no benefit.
- **Large filesort:** ORM `DISTINCT` on large result set with filesort; no index on sort column; P99 = 15s; feature shipped to production without load testing.
- **Stale graph or memory claim:** prior agent trajectory says an index already covers the query, but current ORM SQL changed predicates and sort order; output trusts the old claim, skips plan evidence, and ships a regression.

# Output Contract

Return a query optimization plan with:

- `mode_selected` (slow-query diagnosis / new or changed read path / index lifecycle change / pagination correction / write-heavy production tradeoff)
- `query_scope` (service/repository/report/API surface, target tables, SQL or ORM call sites, and current source files inspected)
- `source_evidence` (current schema/index definitions, repository graph, project memory, execution trajectory, telemetry, slow-query logs, or execution plans inspected with freshness limits)
- `target_queries` (SQL text or ORM equivalent; call site; estimated call frequency)
- `current_execution_plan` (EXPLAIN ANALYZE output; identified bottlenecks)
- `plan_evidence_quality` (representative data volume, statistics freshness, parameter/sample assumptions, and evidence gaps)
- `proposed_indexes` (index name, table, columns in order, partial condition if any, type; named query served)
- `rejected_indexes` (alternatives considered; why rejected)
- `composite_index_rationale` (column order justification: selectivity, predicate type, sort direction)
- `covering_index_columns` (if applicable: filter cols, sort cols, include cols)
- `write_amplification_estimate` (table write rate × per-row cost; acceptable? vs read benefit)
- `expected_execution_plan` (predicted EXPLAIN output after index; Index Scan confirmed)
- `migration_build_plan` (CONCURRENTLY / ONLINE; estimated build time on prod data size; rollback plan)
- `pagination_strategy` (keyset/cursor/offset; query pattern; index to support it)
- `observability` (pg_stat_user_indexes monitoring; slow query threshold; latency SLO)
- `tests` (query execution time before/after; execution plan verification; write latency regression test)
- `changed_query_to_validation_map` (each query/index/pagination change mapped to plan verification, latency check, monitoring, or residual risk)
- `handoff_boundaries` (migration, repository persistence, profiling, API contract, observability, or reliability work that belongs elsewhere)
- `evidence_limits` (what the plan proves and does not prove about production load, real data distribution, write impact, and downstream consumers)

# Evidence Contract

Close an indexing-query-optimization change only when the output names selected mode, query scope, current source and schema evidence inspected, memory/graph/trajectory freshness when used, before/after plan evidence or a not-verified disclosure, write amplification, migration/rollback path, changed-query-to-validation map, evidence limits, residual risk, and next handoff owner. "Add an index" or "query should be faster" is not sufficient evidence.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak optimization plans usually add an index without naming the query, rely on dev-data timing, ignore write cost, miss N+1 fan-out, use offset pagination on large tables, or skip migration/monitoring. Improved outputs must name mode, source evidence, representative plan quality, rejected alternatives, write tradeoff, validation mapping, and handoff boundaries while keeping detailed benchmark matrices in references.

# Routing Coverage

Route here when the primary work is SQL/ORM read-path optimization, index selection, pagination performance, or execution-plan evidence. Guard against over-routing by handing off when the primary concern is domain data shape (`data-model-design`), relational engine operations beyond a target query (`relational-database`), NoSQL partition/index design (`nosql-database`), migration mechanics (`data-migration-design`), initial bottleneck discovery (`profiling`), or ongoing SLO/alerting (`reliability-observability-gate`).

# Quality Gate

The optimization plan is complete only when:

1. Every proposed index is tied to a named query with SQL text.
2. Execution plan obtained on representative data volume (not dev/empty table).
3. Composite index column order justified: selectivity analysis, predicate types, sort direction.
4. Write amplification estimated for write-heavy tables; deemed acceptable.
5. Online index build strategy confirmed for tables > 1M rows in production.
6. Offset pagination replaced or disclosed as unsafe for tables > 100K rows.
7. pg_stat_user_indexes or equivalent monitoring planned for post-deploy index usage confirmation.
8. N+1 query patterns checked and resolved (eager loading vs index).
9. ANALYZE planned after any bulk data load affecting query statistics.
10. Tests include: execution plan verification, latency measurement, write regression test.
11. Selected mode, query scope, source evidence, and plan-evidence quality are explicit.
12. Project memory, repository graph, and execution trajectory evidence are source-confirmed or marked not verified.
13. Each changed query, index, or pagination strategy maps to a validator, monitoring signal, or named residual risk.
14. Handoff boundaries and evidence limits are named so the plan is not over-claimed as live production proof.

# Used By

- data-middleware-change-builder
- reliability-observability-gate

# Handoff

Hand off to `repository-persistence` when the fix is ORM query shape, eager loading, batching, or repository call placement; `profiling` when the database query is not yet proven as the bottleneck; `data-migration-design` for large index build/drop procedure; `data-model-design` for schema and normalization decisions; `performance-budgeting` for latency/write-cost thresholds; `reliability-observability-gate` for slow-query alerting and SLO impact; `api-contract-design` or `frontend-api-integration` when pagination semantics affect clients; and `search-analytics-design` when the query requires full-text search or OLAP capabilities.

# Completion Criteria

The capability is complete when **every index change is tied to a named query, verified against an execution plan on production-scale data, has a calculated write amplification cost, uses a safe online build procedure, and has post-deploy monitoring for index usage confirmation** — with no blind indexes, no blocking builds on live tables, and no offset pagination on large tables.
