# Search Analytics Design Benchmarks And Patterns

Load this reference when search relevance, analytical grain, derived-data ingestion, permission filtering, freshness, drift, reindex, or metric correctness changes. Do not load it when a bounded indexed query in the source store is sufficient.

## Engine And Authority Fit

| Need | Candidate | Required proof before adding it |
| --- | --- | --- |
| Bounded lookup/prefix/full text | Current relational index or extension. | Data/query plan, relevance need, latency/load budget, and why current store is insufficient. |
| Relevance, analyzers, synonyms, typo tolerance, facets | Search engine. | Query/judgment set, analyzer/mapping, permission filter, freshness, reindex, and operations owner. |
| Large scans, rollups, or analytical joins | Columnar/warehouse/read model. | Metric grain, dimensions/measures, volume, partitioning, late data, reconciliation, and cost. |
| Streaming analytics | Stream-ingested analytical store. | Event identity, dedupe, watermark/late correction, lag objective, and replay. |
| Semantic/vector retrieval integration | Existing database extension or vector/search engine after AI lifecycle authority is assigned. | Search owns corpus, retrieval, permission-before-retrieval, deletion/freshness, and fallback integration; `ai-product-extension` owns model/embedding selection, evaluation, and lifecycle acceptance; `data-migration-design` and `delivery-release-gate` own actual cutover/deployment execution. |

Name whether each index/table/model is authoritative, derived, or mixed. Mixed authority requires an explicit owner and conflict rule. Derived data records its source writers, ingestion trigger, idempotency/dedupe, ordering/late-arrival rule, deletion/visibility propagation, user stale behavior, and operator repair path.

## Security, Relevance, And Metric Failure

- Apply tenant/owner/visibility policy inside the shared query builder or engine security before results, counts, facets, aggregations, or retrieval reach the caller. UI/post-generation filtering is not an authorization boundary.
- Give deleted, private, corrected, or erased records an owned tombstone, update, or suppression path within the current policy window.
- Do not rely on periodic full rebuild when prohibited data may remain discoverable.
- Relevance changes use a current query set with graded/expected outcomes and before/after tradeoffs. Click signals are biased leads unless position, segment, freshness, and product objective are accounted for.
- Analytical metrics name grain, entity/time identity, dedupe key, dimensions/measures, timezone/currency, late-arrival correction, source reconciliation, freshness timestamp, and decision owner.
- Analyzer, mapping, schema, or metric-semantic changes define a versioned build/backfill and controlled alias/view transition when in-place mixing would be unsafe. For model/embedding changes, `ai-product-extension` selects and evaluates the lineage and supplies lifecycle acceptance; search validates corpus, permissions, freshness, fallback, and retrieval integration across the transition. Actual build/backfill, cutover, and deployment execution remains with `data-migration-design` and `delivery-release-gate`.

## Rebuild, Evidence, And Limits

Build derived versions from source truth or an owned replayable log.
Before cutover, compare scoped counts, required fields, sampled checksums, relevance or metric deltas, deletion behavior, and performance.
Derive a bounded rollback or containment window from recovery need and ownership.
After cutover, monitor lag, errors, drift, result or metric deltas, capacity, and cost.

When closure uses repository inspection, limit search or analytics claims to inspected mappings and consumers. Treat production behavior as unverified until named live or owner evidence covers it. Synthetic corpus and load tests do not prove real traffic or decision accuracy. State these limits and owners.

Reject engine-by-fashion, global facet counts, UI-only permissions, and in-place analyzer changes without rebuild evidence. Also reject metrics without grain/dedupe, deletion postponed to periodic reindex, manual-only drift checks, and derived state presented as authoritative without revalidation.

Route relational query alternatives to `indexing-query-optimization` and source ownership to `data-model-design`.
Route non-relational primary design to `nosql-database`.
Route model/embedding selection, evaluation, and lifecycle acceptance to `ai-product-extension`; keep corpus, retrieval, permissions, freshness, and fallback integration here.
Route ingestion and replay to `message-queue-design` or `data-side-effect-flow-tracing`.
Route actual data/index/model cutover, backfill, and deployment execution to `data-migration-design` and `delivery-release-gate`; AI lifecycle acceptance does not transfer that execution authority.
Route privacy to `security-privacy-gate` and lag, drift, or capacity to `reliability-observability-gate`.
