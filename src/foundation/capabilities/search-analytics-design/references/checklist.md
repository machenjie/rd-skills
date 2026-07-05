# Search Analytics Design Checklist

- Confirm search or analytics engine use is justified by full-text, relevance, faceting, complex filtering, or OLAP.
- Identify source of truth, indexed fields, transformations, and derived-data owner.
- Define ingestion path, freshness target, late-arrival handling, and failure behavior.
- Define query semantics, relevance checks, filters, facets, permissions, and tenant scope.
- Define reindex or backfill strategy, drift detection, and reconciliation.
- Define fallback when index, ingestion, or analytics pipeline is unavailable.
- Define observability for freshness, index errors, missing documents, and query latency.
- Test stale data, deleted data, permission changes, reindex, and metric correctness.
