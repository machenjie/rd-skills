# Search Analytics Design Checklist

- Classify each changed surface as authoritative, derived, or mixed; name source writers, conflict authority, allowed writes, and caller revalidation.
- Define document/event identity, deduplication, ordering, late correction, deletion/visibility propagation, replay, and backfill overlap.
- Enforce tenant/owner/role/visibility scope for results, counts, facets, aggregations, retrieval, rebuild, fallback, support, and exports.
- Derive the freshness objective and stale behavior from product-decision consequences and measured source-change, ingestion, and query-visible timestamps.
- For search, version mapping, analyzer, and non-model ranking changes and compare current segmented judgment cases plus failure behavior.
- For semantic/vector retrieval, record the `ai-product-extension`-owned model/embedding selection, evaluation, and lifecycle acceptance; verify search-owned corpus, retrieval, permissions, freshness, fallback, and lineage integration.
- For analytics, define grain, entity/event-time identity, dedupe, dimensions/measures, timezone/currency, correction/retraction, and source reconciliation.
- Define in-place or versioned rebuild requirements from compatibility, reversibility, validation, fallback, containment or rollback, and cleanup evidence; assign actual cutover, backfill, and deployment execution to `data-migration-design` and `delivery-release-gate`.
- Map authority, permission, freshness, relevance/metric, and rebuild claims to current evidence, proof limits, and named owners.
