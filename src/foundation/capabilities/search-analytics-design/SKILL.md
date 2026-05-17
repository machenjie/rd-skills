---
name: search-analytics-design
description: Selects search or analytics engines only when full-text, relevance, filtering, faceting, or OLAP needs justify them, with freshness and reindex plans.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "51"
changeforge_version: 0.1.0
---

# Mission

**Design search and analytics engines as purpose-built, derived read systems** — justified only when full-text relevance, complex faceting, OLAP aggregation, or event analytics cannot be served adequately by the source-of-truth database — with explicit definitions of freshness targets, ingestion paths, reindex strategies, permission enforcement in the engine, drift detection, fallback behavior, and schema governance, so that derived views remain consistent with their sources and never become unauthorized disclosure surfaces.

# When To Use

Use this capability when: a change requires full-text search with relevance ranking (Elasticsearch, OpenSearch, Solr, Typesense); faceted navigation with multi-dimensional filtering that a relational database cannot serve at acceptable latency; OLAP aggregation (ClickHouse, BigQuery, Redshift, Snowflake, DuckDB); event-based analytics with dimensional rollups (Apache Druid, Apache Pinot, Databricks); or a new projection/read model needs to be built from event streams to answer analytical queries not served by the transactional store. Also use when an existing search or analytics system needs a schema change, reindex, or freshness SLO revision.

# Do Not Use When

Do not use this capability when: a relational `LIKE` query, full-text index (`tsvector` in PostgreSQL, `FULLTEXT INDEX` in MySQL), or a well-indexed range query can serve the product need at acceptable cost and latency (use `indexing-query-optimization` instead); only read latency reduction is needed without relevance, faceting, or OLAP requirements (use `cache-design`); the primary question is source-of-truth data modeling (use `data-model-design`); or the analytical query can be answered by an existing read model without a new engine.

# Non-Negotiable Rules

- **A search or analytics engine is a derived view, not a source of truth.** The source of truth must be explicitly named. The derived system is allowed to lag, contain stale data, and lose documents during reindex — but the product behavior for each of these degraded states must be explicitly defined. "Derived view" must be enforced architecturally: no write path writes to the search index first and the source-of-truth database second.
- **Permission enforcement must happen in the engine query or in post-query filtering — never implicitly.** A search index that contains documents from multiple tenants or multiple permission levels must enforce tenant isolation and permission filtering in every query. A "global search" feature that returns results from a `_all` index without permission filters is an unauthorized disclosure risk. The permission filter must be part of the query contract, not an after-thought.
- **Freshness must be a product decision with a defined SLO.** "Eventually consistent" is not a freshness SLO. A freshness SLO is: "Search results reflect source data within 30 seconds at p95." Product must sign off on the freshness window. If freshness is safety-critical (e.g., search results affect pricing, inventory availability, or eligibility), the engine is not appropriate unless near-real-time ingestion (Kafka/Kinesis + Kafka Connect + index streaming) is used and the SLO is verified.
- **Reindex strategy must be blue-green or zero-downtime.** A reindex that requires taking the search endpoint offline is a breaking change. Required reindex patterns: (1) build new index from scratch while old index serves queries; (2) atomic alias swap when new index is validated; (3) old index retained for rollback window. A reindex that modifies the existing index in place is only acceptable for additive field changes with no analyzer change.
- **Schema changes to the index must be governed.** Changing an analyzer, changing a field from `keyword` to `text`, changing a field mapping, or renaming a field requires a full reindex — not an incremental update. These are breaking changes to relevance and must be reviewed as rigorously as database migrations.
- **Drift detection and reconciliation are required for any ingestion pipeline.** The difference between document count in the source and document count in the index must be measurable. Missing documents due to ingestion failures, schema rejections, or pipeline restarts must be detectable and backfillable. A silent drift of 3% in search results is a product defect and a trust violation.

# Industry Benchmarks

Anchor against: **Elasticsearch / OpenSearch documentation** — analyzer design (standard, language-specific, custom n-gram), field mapping types (text vs. keyword vs. date vs. nested), query DSL (multi_match, bool, function_score, collapse), index aliases for zero-downtime reindex, index lifecycle management (ILM). **Apache Kafka / Kafka Connect** — CDC (Debezium) for near-real-time ingestion from relational sources; exactly-once semantics considerations; consumer lag as a freshness proxy. **Apache Druid / ClickHouse / BigQuery** — columnar storage; partition pruning; materialized views; time-series aggregation; approximate queries (HyperLogLog for cardinality, t-digest for percentiles). **Snowflake / Databricks** — ELT patterns; dbt for transformation governance; data quality checks (Great Expectations, dbt tests). **OWASP — Broken Access Control (A01:2021)** — multi-tenant search must enforce tenant isolation per query; failure to filter by tenant in search queries is an unauthorized disclosure vulnerability. **Google — Site-Specific Search Design** — search relevance signals (TF-IDF vs. BM25 vs. semantic/dense retrieval); result freshness vs. relevance trade-offs. **GDPR Article 17 (Right to Erasure)** — documents containing personal data that are deleted from the source must be deleted or suppressed from the search index within the legally required window; reindex alone is not sufficient — real-time deletion or tombstone must be supported.

### Search/Analytics Engine Selection Matrix

| Requirement | PostgreSQL Full-Text / LIKE | Elasticsearch / OpenSearch | ClickHouse / BigQuery | Kafka + Druid/Pinot |
| --- | --- | --- | --- | --- |
| Full-text relevance ranking | Adequate (BM25 via `ts_rank`) | Excellent (BM25, custom scoring) | Poor | Poor |
| Faceted multi-dimensional filter | Adequate (with GIN index) | Excellent (aggregations) | Good (GROUP BY) | Good |
| OLAP aggregation / rollups | Poor (slow at scale) | Adequate (limited) | Excellent | Excellent |
| Near-real-time freshness | Excellent (reads source) | Good (with CDC/Kafka) | Adequate (batch) | Excellent (streaming) |
| Semantic / vector search | Via pgvector extension | Via dense_vector / kNN | Not native | Not native |
| Horizontal scale at >10M docs | Poor | Good | Excellent | Excellent |
| Permission filtering complexity | Excellent (SQL) | Adequate (document-level security) | Good | Complex |
| Operational complexity | Low | Medium | Medium-High | High |

### Freshness and Ingestion Path Decision Tree

```
Is the product SLO for freshness < 10 seconds?
  YES → Streaming ingestion required (Kafka CDC via Debezium, or event-driven indexer)
        Document-level deletion must be tombstoned within the same SLO
  NO  → Continue

Is freshness < 5 minutes acceptable?
  YES → Near-real-time batch (polling-based indexer, CDC with small batch window)
  NO  → Continue

Is freshness < 60 minutes acceptable?
  YES → Scheduled batch ingestion (cron-based ETL with drift detection)
  NO  → Source-of-truth database serves the read directly (engine unjustified at this freshness requirement)

Is GDPR Right to Erasure in scope?
  YES → Real-time deletion path required (tombstone or partial update API)
        Scheduled reindex alone is NOT compliant
  NO  → Periodic reindex acceptable for deletions
```

# Selection Rules

Select this capability when **full-text relevance, complex faceting, OLAP aggregation, or streaming event analytics is the explicit product requirement**. Route elsewhere when: the relational database can serve the query with added indexes (use `indexing-query-optimization`); only read latency is the concern (use `cache-design`); source-of-truth data design is the primary need (use `data-model-design`); or the data pipeline architecture needs design before the engine choice (use `data-migration-design` for backfill planning).

# Risk Escalation Rules

Escalate immediately when: a search query does not filter by tenant or permission level (unauthorized disclosure risk — OWASP A01:2021, escalate to `security-privacy-gate`); a search index contains personal data subject to GDPR Article 17 and no real-time deletion path exists (legal compliance risk — escalate to legal/privacy owner); a reindex is planned that requires downtime to a production search endpoint (breaking change — escalate to `delivery-release-gate`); analytics metrics directly affect billing, pricing, or SLA calculation (correctness is a financial obligation — escalate to the data governance owner); or ingestion pipeline lag has exceeded the product-approved freshness SLO without a user-visible staleness indicator.

# Critical Details

- **Permission filtering in search engines is easy to forget and hard to audit.** A multi-tenant application that stores all tenant documents in a shared Elasticsearch index must include `{ "term": { "tenant_id": "current-tenant" } }` (or equivalent document-level security) in every query. A developer who forgets the filter during a new query implementation silently exposes all tenants' data. The permission filter must be in a shared query builder that cannot be bypassed.
- **Analyzer changes are breaking schema changes.** Changing the analyzer for a field (e.g., from `standard` to `english` stemmer) changes how tokens are stored. Documents indexed before the change are stored with the old tokens; new queries use the new token format — relevance breaks silently. The only fix is a full reindex. Treat analyzer changes as schema migrations requiring the same review discipline as database DDL changes.
- **Reindex does not satisfy GDPR Right to Erasure in real time.** If a user requests deletion and the next scheduled reindex is in 6 hours, the deleted user's data remains discoverable via search for 6 hours. For products with GDPR obligations, real-time deletion (tombstone document, update by query, or partial update to null sensitive fields) must be implemented alongside the scheduled reindex path.
- **Search results that affect eligibility, pricing, or inventory must enforce freshness.** A search for "available products" that can return out-of-stock items due to ingestion lag is a product defect. A search for "eligible users" that can return ineligible users due to lag is a compliance defect. For safety-critical freshness, either use the source-of-truth directly for the eligibility check, or add a real-time source-of-truth verification after the search returns candidates.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Multi-tenant search query with no tenant_id filter | All tenant documents returned to any authenticated user; unauthorized disclosure | `term: { tenant_id: current_tenant_id }` in every query builder; shared method that cannot be bypassed |
| Reindex modifies existing index in place after analyzer change | Old documents stored with old tokens; new documents with new tokens; relevance broken for mixed-vintage corpus | Build new index; validate; atomic alias swap; retain old for rollback |
| "Eventually consistent" freshness with no SLO or user signal | Product disputes; user confusion; eligibility defects; SLA violations | Product-approved freshness SLO; staleness indicator in UI when lag > SLO |
| GDPR deletion handled only by periodic reindex (hourly) | Deleted user's data discoverable via search for up to 1 hour; GDPR violation | Real-time delete-by-query or tombstone on the deletion event path |
| Analytics dashboard counts duplicate events | Revenue metrics inflated; executive decisions based on wrong numbers | Deduplication key in event schema; idempotent event ingestion; reconciliation check |
| Search engine used as source of truth for order status | Order status update written to search index first; DB write fails; search shows status that DB does not reflect | DB is always source of truth; search index is derived; no write path touches search before DB |

# Failure Modes

- Multi-tenant search returns cross-tenant results; security incident discovered in audit.
- Analyzer changed in place; BM25 relevance degraded for 60% of queries; no alert; discovered by user complaints.
- Reindex takes 4 hours; search endpoint returns stale/empty results; no blue-green index strategy.
- GDPR deletion not applied to search index; deleted user data returned in search results 3 days later.
- Ingestion pipeline failure silently drops 12% of documents; drift not detected; product shows fewer results than exist.
- Analytics dashboard double-counts events due to at-least-once delivery without deduplication; revenue report inflated by 8%.

# Output Contract

Return a search or analytics design with:

- `engine_justification` (why relational/cache is insufficient; specific requirement that justifies the engine)
- `source_of_truth` (named system; write path; derived-view contract)
- `indexed_fields` (per field: name, type, analyzer/tokenizer, nullable, PII flag)
- `ingestion_path` (sync method: CDC/streaming/polling/batch; tools; failure handling; backpressure)
- `freshness_slo` (product-approved target; measurement method; staleness signal in UI)
- `permission_enforcement` (per query: tenant filter, permission filter, shared query builder location)
- `reindex_strategy` (blue-green alias swap; validation steps; rollback plan; downtime: none)
- `drift_detection` (source vs. index count comparison; alert threshold; reconciliation procedure)
- `gdpr_erasure_path` (real-time deletion or tombstone method; compliance window)
- `schema_governance` (breaking vs. additive change classification; review requirement)
- `fallback_behavior` (behavior when search is unavailable: degrade to source-of-truth query, show stale, or error)
- `observability` (ingestion lag metric, document count delta, query error rate, relevance A/B flag)

# Quality Gate

The design is complete only when:

1. Engine use is justified against the selection matrix (relational/cache cannot serve the requirement).
2. Source of truth is named; derived-view contract is explicit.
3. Permission filtering is in every query path via a shared, non-bypassable method.
4. Freshness SLO is product-approved and measurable.
5. Reindex strategy is blue-green with alias swap and rollback plan.
6. Drift detection is defined with alert threshold.
7. GDPR erasure path is real-time (if PII is indexed).
8. Schema/analyzer changes are classified as breaking or additive.
9. Fallback behavior is defined for engine unavailability.
10. Observability covers ingestion lag, document delta, query error rate.

# Used By

- data-middleware-change-builder
- experience-impact-modeler

# Handoff

Hand off to `indexing-query-optimization` when the relational database can be tuned to serve the query; `data-migration-design` for reindex or backfill work planning; `security-privacy-gate` for permission and GDPR compliance review; `reliability-observability-gate` for freshness SLO and drift alert design; `delivery-release-gate` for reindex deployment coordination.

# Completion Criteria

The capability is complete when **the search or analytics design is justified, the permission model is enforced in every query path, freshness is product-approved with a measurable SLO, reindex is zero-downtime, GDPR erasure is real-time for PII, and drift is detectable before it affects product quality**.
