# Indexing Query Optimization Benchmarks And Patterns

Use this reference when the capability output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, evidence, and quality gates.

## Benchmark Anchors

- PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS)`, `pg_stat_statements`, `pg_indexes`, and `pg_stat_user_indexes` for plan, normalized slow-query, and index-usage evidence.
- MySQL: `EXPLAIN FORMAT=JSON`, slow query logs, and `performance_schema` for key selection, row estimates, filesort, temporary table, and runtime wait evidence.
- Use The Index, Luke and SQL Performance Explained: composite index rules, range-condition limits, keyset pagination, and index-only scan reasoning.
- Designing Data-Intensive Applications: B-tree, LSM-tree, write amplification, compaction, and storage-engine tradeoffs.
- Percona tooling: `pt-query-digest` for MySQL slow-query aggregation and recurring-query prioritization.
- Production migration practice: online/concurrent index builds, invalid-index cleanup, lock-duration review, and rollback/disable path.

## Index Type Selection Matrix

| Query or data pattern | Recommended index | Evidence required | Watchouts |
| --- | --- | --- | --- |
| Equality plus range or sort | Composite B-tree | Predicate order, selectivity, sort direction, plan scan type | Range predicates can stop use of later columns for filtering/sort. |
| Covering read path | B-tree plus `INCLUDE` where supported | SELECT columns, heap fetch count, index size | Covering too many columns bloats writes and cache. |
| Sparse active subset | Partial B-tree with `WHERE` condition | Query predicate always includes partial condition | Predicate mismatch makes the partial index invisible. |
| Case-insensitive lookup | Functional index on normalized expression | Query uses the same expression, e.g. `lower(email)` | Collation and locale rules must match product semantics. |
| Time-series append-only scan | BRIN or partition-local B-tree | Physical ordering correlation, range selectivity | BRIN is weak when physical order does not match filter order. |
| JSONB or array containment | GIN | Operator evidence such as `@>`, `?`, `?|`, `?&` | High build cost and write cost; avoid for incidental JSON fields. |
| Full-text search | GIN on `tsvector`, or search engine handoff | Ranking/relevance requirement and query operator | Route to `search-analytics-design` when relevance/faceting is primary. |
| Geospatial lookup | GiST/SP-GiST where supported | Operator and selectivity, e.g. bounding box or distance | Requires geospatial extension and domain-specific validation. |

## Query Plan Analysis Checklist

Before proposing an index:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <query>;
```

Check these plan signals:

- Index Scan or Index Only Scan is used for the target table when the predicate is selective.
- Sequential scan on a large table with a selective predicate is explained or rejected.
- Nested Loop with sequential scan on the inner side is checked for N+1 or missing foreign-key index.
- Sort or filesort is checked against the desired index order.
- Estimated rows versus actual rows are close enough for the decision; severe mismatch triggers `ANALYZE` or statistics review.
- Bitmap Heap Scan recheck cost is acceptable for the selectivity and table size.
- Buffers read/hit and total execution time are compared before and after.
- Production or representative data volume is named; dev/empty-table plans are marked not verified.

After adding an index:

- Re-run the same plan with the same parameters and representative data.
- Confirm the new plan uses the intended index for the named query.
- Compare actual runtime, buffer reads, scanned rows, and sort behavior.
- Monitor usage with `pg_stat_user_indexes`, equivalent MySQL usage data, or application query telemetry.
- Treat unused indexes after an agreed observation window as removal candidates, especially on write-heavy tables.

## Pagination Comparison

| Method | Query pattern | Performance at depth | Stability | Use when |
| --- | --- | --- | --- | --- |
| Offset | `LIMIT 20 OFFSET N` | O(N), degrades as page depth grows | Unstable under inserts/deletes | Small tables or required page-number navigation. |
| Keyset or seek | `WHERE (ts, id) < ($last_ts, $last_id)` | O(log N) with matching index | Stable with deterministic tie-breaker | Large tables, infinite scroll, API cursors. |
| Opaque cursor | Encoded keyset values | Same as keyset | Stable if cursor includes tie-breaker | Public APIs that should hide physical columns. |
| Deferred join | Join full rows after selecting ordered ids | Better than plain offset | Still unstable under writes | Legacy page-number UX when keyset is not feasible. |

## Evidence Patterns

- Slow-query repair: telemetry identifies the normalized query, plan shows scan/sort cost, proposed index maps to one query, and before/after plan proves the improvement.
- New read path: repository method or SQL builder is inspected, query predicates and sort order are stable, index plan is justified, and pagination semantics are compatible with callers.
- Index drop: usage evidence covers a sufficient window, undocumented callers are searched, rollback path is documented, and post-drop monitoring is defined.
- N+1 repair: trace shows query count per request, ORM call site is fixed through eager loading or batching, and any remaining index need is separately justified.
- Write-heavy table: read benefit is compared with write rate, storage growth, maintenance/vacuum overhead, build risk, and SLO budget.

## Anti-Patterns To Reject

- Index on every filterable column with no named query.
- Index proposed from a plan on a 100-row dev table while production has millions of rows.
- Offset pagination on deep pages with no table-size disclosure.
- Low-cardinality leading column on a broad query.
- N+1 query fan-out treated as an index-only issue.
- Dropping an index after a short or non-representative quiet period.
- Blocking index build on a hot production table without lock evidence.
