# Search Analytics Design Benchmarks And Patterns

Use this reference when `search-analytics-design` needs more detail than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, source-of-truth boundaries, evidence, output, and quality gates; use this file for engine selection, relevance and metric validation, ingestion/deletion patterns, drift/reconciliation, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- Elasticsearch and OpenSearch: analyzer design, field mapping, query DSL, function scoring, aliases, index lifecycle management, and zero-downtime reindex.
- Apache Solr and Typesense: relevance tuning, facets, synonyms, typo tolerance, and schema governance.
- PostgreSQL full-text and pgvector: simpler alternatives for smaller full-text, ranking, or vector workloads before adding an external engine.
- ClickHouse, Druid, Pinot, BigQuery, Snowflake, DuckDB, and Databricks: OLAP grain, partitioning, materialized views, approximate aggregates, and scan-cost control.
- Kafka, Kafka Connect, Debezium, and event-driven indexers: CDC, replay, consumer lag, idempotent ingestion, late arrivals, and deletion/tombstone propagation.
- dbt tests, Great Expectations, and reconciliation queries: metric correctness, uniqueness, not-null, accepted values, row count, and source-to-derived drift checks.
- OWASP Broken Access Control: tenant, role, owner, and visibility filters must be part of the query contract for shared indexes.
- GDPR erasure and data minimization: indexed personal data needs deletion/suppression within the required window and cannot rely only on periodic reindex.

## Engine Selection Matrix

| Need | Prefer | Evidence required | Watchouts |
| --- | --- | --- | --- |
| Simple contains or prefix filter on small data | Relational index or full-text extension | Query, data size, latency budget, index plan | Do not add external search for a single filter. |
| Relevance ranking, stemming, synonyms, typo tolerance | Search engine | Query corpus, relevance samples, analyzer choice, permission filter contract | Analyzer changes require reindex and relevance validation. |
| Faceted navigation with multi-dimensional filtering | Search engine or columnar store | Filter/facet list, cardinality, result counts, latency target | Facets can leak restricted counts without permission filters. |
| Operational reporting on source tables | Relational replica/materialized view | Query plan, read load, freshness need, source impact | Avoid OLAP engine if read replica is sufficient. |
| Large analytical scans and rollups | Columnar analytics warehouse/store | Grain, dimensions, measures, data volume, partitioning, reconciliation | Metric definitions and late-arrival behavior must be explicit. |
| Streaming dashboards or event analytics | Druid/Pinot/streaming warehouse | Event schema, dedupe key, watermark/late arrival rule, lag SLO | At-least-once delivery can inflate metrics without dedupe. |
| Semantic/vector retrieval | pgvector or search/vector engine | Embedding model/version, permission-aware retrieval, freshness, evaluation set | Retrieval output is derived and may expose stale/deleted data. |

## Derived Data Contract Checklist

- Name the source of truth and every writer that can change it.
- State whether the search/analytics engine is derived, authoritative, or mixed; mixed authority requires explicit data-owner approval.
- Define the ingestion trigger: CDC, event, polling, batch, manual backfill, or replay.
- Define idempotency and dedupe for at-least-once ingestion.
- Define late-arrival behavior and correction windows for analytics.
- Define deletion, visibility-change, and permission-change propagation.
- Define source-to-derived drift check: counts, checksums, sampled documents, or metric reconciliation.
- Define user-facing stale/unavailable behavior and operator-facing recovery.

## Permission And Privacy Review

| Surface | Required contract | Failure to reject |
| --- | --- | --- |
| Shared search index | Tenant/owner/visibility filters in every query builder or engine-level document security. | UI-only filtering or caller-supplied tenant ID without server enforcement. |
| Facet counts | Counts computed after permission filter. | Global counts that reveal hidden categories, tenants, or records. |
| Support/admin search | Actor, scope, purpose, audit event, and least-privilege query. | Admin index with unrestricted fields and no audit. |
| Deleted or private records | Tombstone/delete/update-by-query path within the compliance window. | Waiting for periodic reindex. |
| Analytics events with user data | Data minimization, retention, pseudonymization where needed, and metric-level access control. | Raw PII copied into broad analytics datasets by default. |
| Semantic retrieval | Permission-aware retrieval before generation or display. | Filtering only after model output or answer synthesis. |

## Freshness And Reconciliation Patterns

```text
Need freshness under seconds:
  Use CDC or event stream ingestion.
  Monitor consumer lag, indexing lag, failed writes, and delete/tombstone lag.
  Verify source-of-truth on actions where stale search could cause harm.

Need freshness under minutes:
  Polling or micro-batch can be acceptable.
  Show stale-data behavior when lag exceeds product SLO.
  Reconcile counts and sampled records on a scheduled cadence.

Need hourly/daily analytics:
  Batch ELT can be acceptable.
  Define grain, watermark, late-arrival correction, metric owner, and dashboard freshness timestamp.
  Reconcile headline metrics to source or ledger/reporting authority.
```

## Reindex And Backfill Pattern

- Build new index/table version while old version serves traffic.
- Rebuild from source-of-truth or replayable event log, not from the old derived view unless explicitly justified.
- Validate document count, required fields, permission fields, sample queries, relevance/metric differences, and drift thresholds.
- Cut over with alias/swap/view update or controlled dashboard release.
- Retain old version for rollback window and define cleanup owner/expiry.
- Monitor query errors, lag, result count, and business metric deltas after cutover.

## Graph, Memory, And Trajectory Coupling

Treat graph, memory, and execution trajectory as discovery inputs until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current index schemas, query builders, ingestion jobs, dashboards, tests, and source writers are inspected. | Graph proximity is used as proof that all fields, permissions, or consumers are covered. |
| Project memory | Prior engine or dashboard decision names unchanged sources, indexes, metrics, and owners with freshness evidence. | Memory predates schema, permission, metric, ingestion, or retention changes. |
| Execution trajectory | Reindex, validator, dashboard query, or drift check ran after the final relevant edit. | Output predates current schema/query or covers only a happy-path sample. |
| Telemetry/support signal | Query failure, relevance issue, dashboard dispute, or lag signal maps to current field names and date range. | Signal lacks route/query/index/version/date evidence. |
| Generated assets | Search clients, dashboard models, docs, and generated query code are regenerated or inspected. | Generated files were not refreshed after schema or metric changes. |

Strong outputs state which graph, memory, and trajectory inputs were accepted, rejected, or left unknown.

## Validation Evidence Patterns

- Search relevance: fixed query set, expected top results or graded judgment set, before/after comparison, and accepted relevance tradeoff.
- Permission search: allowed, denied, wrong-tenant, private, deleted, and support/admin queries against the shared query builder or engine security layer.
- Freshness: source update timestamp, ingestion timestamp, query-visible timestamp, p95/p99 lag, and alert threshold.
- Drift: source count versus index count by tenant/visibility/type, sampled document checksum, missing document backfill, and reconciliation owner.
- Analytics metric: metric definition, grain, dedupe key, late-arrival rule, source reconciliation query, dashboard freshness, and guardrail threshold.
- Reindex/backfill: old/new index/table comparison, alias/cutover test, rollback test, and post-cutover monitoring.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Engine selected because "search is faster." | Operational complexity added without relevance/facet/OLAP need. | Prove relational/cache/read-model insufficiency first. |
| Permission filter applied only in UI. | API or query caller can access restricted documents/counts. | Shared server query builder or engine-level security. |
| Facet counts computed globally. | Hidden records or tenants are disclosed through counts. | Compute facets after tenant/permission filter. |
| Analyzer or mapping changed in place. | Old and new tokens coexist; relevance breaks silently. | Versioned index plus full rebuild and alias swap. |
| Analytics metric lacks grain and dedupe key. | Duplicate events inflate decisions and reports. | Define metric contract, dedupe, late-arrival, and reconciliation. |
| Periodic reindex handles deletion. | Deleted or private data remains discoverable until next rebuild. | Tombstone/delete/update path on the source deletion or visibility event. |
| Drift check is manual ad hoc SQL. | Missing documents or wrong metrics persist unnoticed. | Scheduled reconciliation with alert threshold and owner. |
| Project memory reused as schema proof. | Stale fields, permissions, or metrics become design inputs. | Confirm against current source, schemas, tests, dashboards, and owners. |

## Handoff Boundaries

- Use `indexing-query-optimization` when relational indexes or query rewrites can serve the requirement.
- Use `cache-design` when the engine is only proposed for read latency acceleration.
- Use `data-model-design` when the source-of-truth entity, invariant, or ownership model is unresolved.
- Use `nosql-database` when the primary issue is non-relational key/document/table design rather than search relevance or OLAP.
- Use `message-queue-design` or `data-side-effect-flow-tracing` for ingestion ordering, replay, idempotency, and side-effect flow.
- Use `data-migration-design`, `version-compatibility`, or `delivery-release-gate` for live reindex, backfill, cutover, rollback, and mixed-version rollout.
- Use `security-privacy-gate` for tenant isolation, PII, erasure, support/admin access, or semantic retrieval privacy.
- Use `reliability-observability-gate` for freshness SLOs, drift alerts, capacity, lag, and operational recovery.
