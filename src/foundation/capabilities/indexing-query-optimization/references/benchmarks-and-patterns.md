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
| Sparse active subset | Partial B-tree with `WHERE` condition | The named query predicate implies the partial condition for supported parameter shapes | Predicate mismatch makes the partial index invisible. |
| Case-insensitive or normalized lookup | Functional index on the exact query expression | Query and index use the same expression and declare the field's equality and ordering semantics | Use when expression plus collation, locale, case, and accent behavior implements those semantics; preserve exact identity for opaque fields. |
| Time-series append-only scan | BRIN or partition-local B-tree | Physical ordering correlation, range selectivity | BRIN is weak when physical order does not match filter order. |
| JSONB or array containment | GIN | Operator evidence such as `@>`, `?`, `?|`, `?&` | High build cost and write cost; avoid for incidental JSON fields. |
| Full-text search | GIN on `tsvector`, or search engine handoff | Ranking/relevance requirement and query operator | Route to `search-analytics-design` when relevance/faceting is primary. |
| Geospatial lookup | GiST/SP-GiST where supported | Operator and selectivity, e.g. bounding box or distance | Requires geospatial extension and domain-specific validation. |
## Query Plan Analysis Checklist
Before proposing an index, select the current engine/version and its documented plan command. Record whether the selected mode estimates or executes the statement; a command named `EXPLAIN` is not assumed safe across engines or statement classes. Use representative parameters and execute within an approved data, side-effect, lock, and resource boundary. PostgreSQL can provide an estimated plan with `EXPLAIN (FORMAT TEXT)`. Add `ANALYZE, BUFFERS` only when actual execution is safe. MySQL can provide an estimate with `EXPLAIN FORMAT=JSON`. Use execution analysis only when the documented version and safety boundary permit it.

When execution is unsafe or unavailable, retain whichever evidence is available: the estimated plan, bounded normalized-query telemetry, or both. Record why execution was not performed. Mark actual rows, runtime, buffer/cache behavior, waits, and side effects as unverified where applicable. Then check these available signals:
- The engine-specific access or scan operator fits the target table and predicate selectivity.
- A full scan on a large table with a selective predicate is explained or rejected.
- Nested-loop or repeated inner access is checked for N+1 behavior or a missing foreign-key index.
- Sort, filesort, or the engine-equivalent operation is checked against the desired index order.
- Estimated and observed rows are compared when execution evidence is available; severe mismatch triggers the selected engine's statistics review or refresh path.
- Bitmap/recheck or analogous engine-specific work is assessed when the selected plan exposes it.
- Available buffer, cache, IO, scanned-row, and execution-time evidence is compared before and after.
- Production or representative data volume is named; dev/empty-table plans are marked not verified.
After adding an index:
- Re-run the same selected engine/version plan mode with the same parameters and representative data, or repeat the same bounded telemetry comparison when plan execution remains unavailable.
- Confirm the new plan uses the intended access path for the named query.
- Compare applicable estimated or observed rows, access and sort behavior, runtime, buffer/cache or IO, and scanned rows; label unobserved runtime effects explicitly.
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
