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

Do not use this capability for non-relational data store optimization (use `nosql-database` for DynamoDB/MongoDB partition and index design). Do not use it for full-text search optimization (use `search-analytics-design` for Elasticsearch/Solr relevance tuning). Do not add indexes "just in case" — every index has a write amplification cost, a storage cost, and a maintenance burden; justification is mandatory.

# Non-Negotiable Rules

- **Every index must be tied to a named query.** Index justification format: "Index `idx_orders_user_status` exists to serve query: `SELECT ... FROM orders WHERE user_id = $1 AND status = $2 ORDER BY created_at DESC LIMIT 50`." No index without a named beneficiary query.
- **Execution plan is required before and after.** Use `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` (PostgreSQL), `EXPLAIN ANALYZE` (MySQL), or equivalent. Confirm: Seq Scan changed to Index Scan; rows actually scanned match expected selectivity; buffer hits indicate cache usage. Plan estimates on empty/dev tables are misleading — test on production-scale data or realistic data volumes.
- **Composite index column order: most selective first, then equality predicates, then range predicates, then sort column.** For `WHERE status = $1 AND user_id = $2 ORDER BY created_at DESC`: index column order = `(user_id, status, created_at DESC)` — equality predicates first, matching the sort last. A mismatch in column order causes the index to be skipped entirely for sorting and requires a filesort.
- **Write amplification is calculated, not ignored.** For every proposed index on a high-write table: estimate write overhead = (rows written per second) × (index maintenance cost per row per index). A table receiving 5,000 INSERT/s with 5 indexes has meaningful write amplification. If index count is causing write latency SLA risk, the access pattern must be reconsidered.
- **Online index builds for tables > 1 million rows.** PostgreSQL: `CREATE INDEX CONCURRENTLY` — does not hold a lock; takes longer; may fail and leave an invalid index. MySQL: `ALTER TABLE ... ALGORITHM=INPLACE, LOCK=NONE`. Never use `CREATE INDEX` (blocking) on a live production table with significant traffic without confirming the lock duration is acceptable.
- **Offset pagination is forbidden for tables > 100,000 rows without a keyset/cursor alternative.** `OFFSET 10000 LIMIT 20` scans and discards 10,000 rows before returning 20. For large tables this becomes O(N) with N proportional to page depth. Use keyset pagination: `WHERE (created_at, id) < ($last_created_at, $last_id) ORDER BY created_at DESC, id DESC LIMIT 20`.
- **Covering index optimization requires column order discipline.** A covering index that includes all SELECT columns avoids a table heap fetch entirely. Column order: filter columns (equality) → sort columns → include columns (SELECT targets). PostgreSQL supports `INCLUDE` clause for non-key include columns (PostgreSQL 11+) to avoid key bloat.

# Industry Benchmarks

Anchor against: **PostgreSQL documentation** — "Using EXPLAIN" (official guide to interpreting execution plans); `EXPLAIN (ANALYZE, BUFFERS)` for runtime statistics; `pg_stat_statements` for production slow query identification; `pg_indexes` / `pg_stat_user_indexes` for index usage statistics (unused indexes = `idx_scan = 0`). **MySQL EXPLAIN FORMAT=JSON** — `key`, `key_len`, `rows`, `Extra: Using filesort` (sort not covered by index), `Extra: Using index` (covering index hit). **Use The Index, Luke** (Winand, use-the-index-luke.com) — definitive practical guide to SQL index design; B-Tree structure; composite index column selection; range conditions break index usage for subsequent columns. **Kleppmann DDIA** (Ch. 3) — B-Tree vs LSM-Tree trade-offs; write amplification; SSTables; compaction. **Markus Winand "SQL Performance Explained"** — composite index predicates; three-star index system; partial indexes; index-only scans. **Percona pt-query-digest** — MySQL slow query log analysis and aggregation. **pg_partman** — PostgreSQL table partitioning by range/list; reduces index scan scope for time-series data. **Partial indexes** (PostgreSQL) — `CREATE INDEX idx_active_users ON users (email) WHERE deleted_at IS NULL` — smaller index; faster scans; useful for filtered queries on a subset of rows. **Functional indexes** (PostgreSQL) — `CREATE INDEX idx_email_lower ON users (lower(email))` for case-insensitive lookups. **BRIN indexes** (Block Range INdexes) — PostgreSQL; efficient for physically ordered large tables (timestamps, sequential IDs); tiny compared to B-tree; suitable for time-series append-only tables. **GIN indexes** — PostgreSQL; for array contains, JSONB key search, full-text search; high build cost; suitable for read-heavy JSONB querying. **Keyset pagination** (also called seek method; Winand) — `WHERE (col1, col2) < (last_val1, last_val2)` with matching composite index; O(log N) at any depth; stable under inserts/deletes.

### Index Type Selection Matrix

| Data type / query pattern | Recommended index | Notes |
| --- | --- | --- |
| Equality + range on columns (most common) | B-Tree composite | Column order: equality cols first, range col last, sort col last |
| Full-text search (PostgreSQL) | GIN on `tsvector` column | `to_tsvector()` stored in generated column; `@@` operator |
| JSONB key/value search | GIN on JSONB column | Supports `@>`, `?`, `?|`, `?&` operators |
| Array contains (`@>`) | GIN on array column | Inverted index; high build cost; excellent read performance |
| Geospatial (PostGIS) | GiST index | `&&` overlap, `<->` distance operators |
| Time-series, append-only (ordered insert) | BRIN | Tiny; effective only when physical row order correlates with query order |
| Case-insensitive text lookup | B-Tree on `lower(column)` | Functional index; query must use `lower()` to match |
| Sparse condition (soft-delete, status filter) | Partial B-Tree with WHERE clause | Only indexes qualifying rows; much smaller |
| UUID primary key (random) | B-Tree; consider UUIDv7 for seq | UUIDv4 causes page splits; UUIDv7 is sequential |

### Query Plan Analysis Checklist

```
Before proposing an index, analyze the execution plan:

PostgreSQL:
  EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <your query>;

Key signals to check:
  ✅ Index Scan or Index Only Scan on the target table
  ⚠️  Seq Scan on a table > 10,000 rows without WHERE clause is expected
  ❌  Seq Scan on a table > 100,000 rows with selective WHERE clause = missing index
  ❌  Nested Loop with Seq Scan on inner side = N+1 or missing FK index
  ❌  Sort (cost=...) without "using index" = sort not covered; add sort column to index
  ❌  "rows=10000 actual rows=1" = severe cardinality estimate error; run ANALYZE
  ❌  Bitmap Heap Scan with high "recheck" = low selectivity index or stale statistics

After adding index:
  EXPLAIN (ANALYZE) re-run: confirm plan changed to Index Scan
  Check actual_rows matches expected selectivity
  Check buffers: blocks hit should increase; blocks read should decrease
  Check total execution time (actual time): measure improvement

Monitor in production:
  SELECT * FROM pg_stat_user_indexes 
  WHERE relname = 'orders' 
  ORDER BY idx_scan DESC;
  -- idx_scan = 0 after 7+ days: unused index candidate for removal
```

### Pagination Method Comparison

| Method | Query pattern | Performance at depth | Stability | Use when |
| --- | --- | --- | --- | --- |
| Offset | `LIMIT 20 OFFSET N` | O(N) — degrades with depth | Unstable under inserts | Small tables (< 100k rows), page number navigation required |
| Keyset (seek) | `WHERE (ts, id) < (last_ts, last_id)` | O(log N) — constant depth | Stable | Large tables, infinite scroll, API cursors |
| Cursor (opaque) | Encoded keyset values in cursor token | O(log N) | Stable | API pagination (GraphQL Relay, REST next_cursor) |
| Deferred join | `SELECT * FROM t JOIN (SELECT id FROM t ORDER BY ... LIMIT 20 OFFSET N) AS sub USING (id)` | Better than plain offset | Unstable | When keyset not feasible; reduces row data access |

# Selection Rules

Select this capability when **query performance, index design, or execution plan analysis** are the primary concern. Adjacent routing:

- Prefer `data-model-design` when the primary concern is schema design, normalization, and relationship modeling.
- Prefer `data-migration-design` when the primary concern is the migration process for adding the index (online build, rollback, gh-ost/pt-osc).
- Prefer `nosql-database` when the primary concern is non-relational data store partition key and secondary index selection.
- Prefer `search-analytics-design` when the primary concern is full-text search relevance, faceted search, or OLAP queries.
- Prefer `reliability-observability-gate` for production slow query alerting and SLO impact review.

# Risk Escalation Rules

Escalate when: an index build is planned on a table > 10 million rows in production (estimate build time and lock duration); a query modification affects a billing, financial reporting, or audit table; an index is being dropped that might be used by undocumented queries; the table is write-heavy (> 1,000 writes/s) and additional index maintenance cost could cause write latency SLA breach; a query plan regression is detected in production (latency P99 increase correlated with a schema change).

# Critical Details

Execution plan estimates on development data diverge significantly from production at scale. Precision failures:

- **Index column order mismatch.** Index: `(status, user_id, created_at)`. Query: `WHERE user_id = $1 AND status = $2 ORDER BY created_at DESC`. PostgreSQL may not use this index for sorting because the leading column `status` has low cardinality (only 3 values) and the planner estimates a partial index scan would be more expensive than a filesort. Correct order: `(user_id, status, created_at DESC)`.
- **Low-cardinality leading column.** A table has `gender` column with values {M, F, X} (3 values; cardinality = 3; each value covers ~33% of rows). An index with `gender` as the leading column will not be selective enough for the planner to use — a sequential scan of 33% of the table is often faster than an index scan + heap fetch. Low-cardinality columns belong after selective columns in composite indexes.
- **Unused indexes on write-heavy table.** A table receives 10,000 inserts/sec. It has 8 indexes that were added incrementally over 2 years. Query pg_stat_user_indexes: 3 of them have `idx_scan = 0` for 30 days. Those 3 indexes are consuming write capacity and disk space with no read benefit. Remove unused indexes on write-heavy tables.
- **N+1 ORM query.** An ORM loads 100 orders. Then for each order, it loads `order.customer.name` — executing 100 additional SELECT statements. Total: 101 queries. This is not an index problem; it is an eager loading problem. Fix with `JOIN FETCH` or `include: ['customer']` in the ORM query. No index can fix N+1.
- **Statistics staleness.** After a bulk import of 5 million rows, PostgreSQL statistics are stale. The planner estimates 1,000 rows but scans 5 million. Run `ANALYZE orders;` after bulk imports. Schedule `autovacuum` appropriately for high-churn tables.

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

- Index added in wrong column order; planner falls back to sequential scan; query 100x slower than expected; detected only in production load test.
- Blocking `CREATE INDEX` on orders table; table locked for 8 minutes; all checkout requests timeout; P0 incident.
- `OFFSET` pagination on audit log table (50M rows); user navigates to page 2,500; query scans 50,000 rows; timeout; CSAT impact.
- N+1 ORM query on customer dashboard; 200 customers loaded + 200 individual account queries; dashboard latency 8s; misdiagnosed as missing index; root cause (eager loading) unaddressed.
- Unused index on write-heavy table; 6 unused indexes on `events` table; INSERT latency increased from 2ms to 12ms; discovered during load test.
- Statistics staleness after bulk import; planner chooses wrong join order; reporting query 30x slower than expected; `ANALYZE` not run post-import.
- Low-cardinality index on `status` column; status = 'active' matches 80% of rows; planner uses sequential scan; index never used; write cost paid with no benefit.
- ORM `DISTINCT` on large result set with filesort; no index on sort column; P99 = 15s; feature shipped to production without load testing.

# Output Contract

Return a query optimization plan with:

- `target_queries` (SQL text or ORM equivalent; call site; estimated call frequency)
- `current_execution_plan` (EXPLAIN ANALYZE output; identified bottlenecks)
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

# Used By

- data-middleware-change-builder
- reliability-observability-gate

# Handoff

Hand off to `data-migration-design` for large index build migration procedure; `data-model-design` for schema and normalization decisions; `reliability-observability-gate` for slow query alerting and SLO impact; `search-analytics-design` when the query requires full-text search or OLAP capabilities.

# Completion Criteria

The capability is complete when **every index change is tied to a named query, verified against an execution plan on production-scale data, has a calculated write amplification cost, uses a safe online build procedure, and has post-deploy monitoring for index usage confirmation** — with no blind indexes, no blocking builds on live tables, and no offset pagination on large tables.
