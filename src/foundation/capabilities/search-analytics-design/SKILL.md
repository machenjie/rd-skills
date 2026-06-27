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

# Stage Fit

Owns data-middleware planning, implementation review, and repair when the primary decision is whether a search index, search service, columnar analytics store, event analytics engine, or derived analytical read model is justified and safe. In planning, it turns product query needs, current source-of-truth boundaries, repository graph, project memory, execution trajectory, query telemetry, and existing read models into an engine decision with freshness, permission, drift, reindex, erasure, fallback, and validation obligations. In coding, bug-fix, debugging, code-review, refactoring, testing, release-readiness, and final handoff, it keeps schema/query/ingestion/freshness/permission decisions mapped to current validation evidence rather than stale memory, graph proximity, or a prior green run. In review, it rejects engine selection by trend, stale project memory, permission filters assumed outside the query contract, unbounded reindex/backfill plans, and analytics metrics that cannot be reconciled to source data. Hand off when the primary question is relational index tuning, cache-only acceleration, domain source modeling, pipeline migration sequencing, security/privacy depth, reliability SLO enforcement, or release orchestration.

# Non-Negotiable Rules

- **A search or analytics engine is a derived view, not a source of truth.** The source of truth must be explicitly named. The derived system is allowed to lag, contain stale data, and lose documents during reindex — but the product behavior for each of these degraded states must be explicitly defined. "Derived view" must be enforced architecturally: no write path writes to the search index first and the source-of-truth database second.
- **Permission enforcement must happen in the engine query or in post-query filtering — never implicitly.** A search index that contains documents from multiple tenants or multiple permission levels must enforce tenant isolation and permission filtering in every query. A "global search" feature that returns results from a `_all` index without permission filters is an unauthorized disclosure risk. The permission filter must be part of the query contract, not an after-thought.
- **Freshness must be a product decision with a defined SLO.** "Eventually consistent" is not a freshness SLO. A freshness SLO is: "Search results reflect source data within 30 seconds at p95." Product must sign off on the freshness window. If freshness is safety-critical (e.g., search results affect pricing, inventory availability, or eligibility), the engine is not appropriate unless near-real-time ingestion (Kafka/Kinesis + Kafka Connect + index streaming) is used and the SLO is verified.
- **Reindex strategy must be blue-green or zero-downtime.** A reindex that requires taking the search endpoint offline is a breaking change. Required reindex patterns: (1) build new index from scratch while old index serves queries; (2) atomic alias swap when new index is validated; (3) old index retained for rollback window. A reindex that modifies the existing index in place is only acceptable for additive field changes with no analyzer change.
- **Schema changes to the index must be governed.** Changing an analyzer, changing a field from `keyword` to `text`, changing a field mapping, or renaming a field requires a full reindex — not an incremental update. These are breaking changes to relevance and must be reviewed as rigorously as database migrations.
- **Drift detection and reconciliation are required for any ingestion pipeline.** The difference between document count in the source and document count in the index must be measurable. Missing documents due to ingestion failures, schema rejections, or pipeline restarts must be detectable and backfillable. A silent drift of 3% in search results is a product defect and a trust violation.
- **Search or analytics safety claims require fresh validation evidence.** A design is not complete until each engine, schema, query, ingestion, freshness, permission, erasure, fallback, relevance, metric, and reindex decision maps to a command, dashboard query, owner review, artifact, report, or residual risk that ran after the final material edit.
- **Validation and support tooling must not create a new disclosure path.** Broad search scans, dashboard exports, warehouse queries, index dumps, reindex scripts, connector reads, or support/admin search tools must record permission state, read-only or dry-run boundary, rollback/revert path, output retention, and redaction rules before results are pasted, stored, or reused as memory.

# Mode Matrix

Select the search or analytics mode before writing the design.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Search engine justification | Full-text relevance, ranking, stemming, synonyms, facets, fuzzy match, semantic/vector retrieval, or cross-field search is requested. | Prove relational indexes or existing read models are insufficient and define derived search behavior. | Query intent, current source/read-model evidence, relevance requirements, rejected relational/cache alternatives. | `indexing-query-optimization`, `data-model-design`, `performance-budgeting` | Engine choice by product label or vendor preference. |
| Analytics engine justification | OLAP, rollups, dashboards, cohort/funnel, event analytics, large scans, or dimensional aggregation is requested. | Separate operational source data from analytical projection and define reconciliation. | Metric definitions, source tables/events, dimensional grain, freshness target, dedupe/reconciliation evidence. | `bigdata-product-extension`, `acceptance-standard-definition`, `quality-test-gate` | Dashboard shape before metric/source contract. |
| Existing engine schema or query change | Analyzer, mapping, field, facet, dimension, rollup, relevance function, or query DSL changes. | Preserve old relevance/contracts while planning reindex/backfill and validation. | Current schema/query, consumers, sample queries, before/after relevance or metric checks, rollback. | `version-compatibility`, `data-migration-design`, `delivery-release-gate` | In-place analyzer or mapping mutation without reindex. |
| Ingestion and freshness design | CDC, streaming, polling, batch ETL, late arrivals, deletion, lag, or drift are in scope. | Make derived data lag measurable, recoverable, and acceptable to product. | Source-of-truth writes, ingestion path, lag SLO, replay/backfill, drift check, staleness behavior. | `message-queue-design`, `data-side-effect-flow-tracing`, `reliability-observability-gate` | "Eventually consistent" with no SLO. |
| Permission, privacy, and deletion review | Tenant, role, visibility, PII, erasure, support/admin search, or shared index is present. | Prevent search/analytics from bypassing source permissions or retaining deleted data. | Actor/resource/scope, query filter contract, erasure/tombstone path, audit and denial evidence. | `permission-boundary-modeling`, `security-privacy-gate` | UI-only filtering or periodic reindex as deletion proof. |
| Validation and handoff closure | A design, review, bug fix, refactor, or release claim depends on current graph, memory, execution output, dashboard query, scanner, or generated artifact. | Prove validation freshness, map each changed decision to evidence, and bound what remains unknown. | Command/report path, validator/tool, exit code or manual result, changed scope, what evidence proves/does not prove. | `validation-broker`, `execution-trajectory-analysis`, `quality-test-gate` | Completion language based on stale or partial checks. |

# Industry Benchmarks

Anchor against Elasticsearch/OpenSearch analyzer, mapping, query DSL, alias-swap, and ILM practice; Kafka/Kafka Connect CDC and consumer lag; ClickHouse, Druid, Pinot, BigQuery, Snowflake, Databricks, and dbt analytical governance; OWASP Broken Access Control for tenant-filtered query contracts; SRE freshness/drift observability; and GDPR erasure expectations for indexed personal data. Keep this body focused on selection, evidence, output, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for engine-selection matrices, relevance/metric validation, ingestion and deletion patterns, graph/memory/trajectory coupling, and anti-pattern review.

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

# Proactive Professional Triggers

- **Signal:** A request says "add search", "analytics dashboard", "facets", "semantic search", or "make reporting faster" without naming the source query, current bottleneck, relevance/metric need, or relational alternative. **Hidden risk:** a new engine becomes unjustified operational complexity. **Required professional action:** prove the engine need or route to relational indexing/cache first. **Route to:** `search-analytics-design`, `indexing-query-optimization`, `cache-design`. **Evidence required:** requirement, existing source/read-model evidence, rejected simpler alternative, and engine justification.
- **Signal:** Repository graph, previous execution trajectory, or project memory suggests an existing index, dashboard, pipeline, or query to reuse. **Hidden risk:** stale engine schema, renamed fields, changed permission model, or old metric definitions are treated as current truth. **Required professional action:** confirm with current source, schema, ingestion jobs, tests, dashboards, and owners before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected reuse, freshness limit, and evidence limits.
- **Signal:** Search or analytics results include tenant, role, visibility, entitlement, personal data, deletion, or support/admin behavior. **Hidden risk:** derived systems disclose restricted or deleted data even when source systems are correct. **Required professional action:** make permission and erasure enforcement part of the query/ingestion contract. **Route to:** `permission-boundary-modeling`, `security-privacy-gate`. **Evidence required:** actor/resource/action/scope, filter contract, tombstone/delete path, and denied/deleted validation.
- **Signal:** Reindex, backfill, analyzer change, mapping change, dimension change, metric definition change, or alias swap is proposed. **Hidden risk:** relevance, dashboards, or consumers break during mixed old/new data. **Required professional action:** require blue-green/replay/backfill plan with validation and rollback. **Route to:** `data-migration-design`, `version-compatibility`, `delivery-release-gate`. **Evidence required:** old/new schema, validation comparison, cutover, rollback, and retained old index/window.
- **Signal:** Freshness is described as "eventual", "daily", "near real time", or "batch" without product-approved SLO and lag measurement. **Hidden risk:** users and decision makers act on stale or misleading derived data. **Required professional action:** define freshness SLO, staleness behavior, lag metric, alert, and reconciliation. **Route to:** `performance-budgeting`, `reliability-observability-gate`, `quality-test-gate`. **Evidence required:** lag SLO, measurement source, staleness indicator, drift check, and validation command.
- **Signal:** Prior validation, repository graph, project memory, dashboard output, generated client/model, or execution trajectory says a search index, analytics metric, permission filter, drift check, or freshness SLO is safe before schema, query, ingestion, metric, visibility, or generated artifact changes. **Hidden risk:** stale proof certifies the wrong field names, data grain, permission model, or index version. **Required professional action:** rerun or downgrade the proof, inspect current source and generated artifacts, and record validation freshness. **Route to:** `validation-broker`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability. **Evidence required:** changed path, validator/report path, exit code or manual artifact, what stale evidence no longer proves, and residual risk owner.
- **Signal:** A validation, debugging, support, export, reindex, backfill, warehouse, connector, or search-admin command can print restricted rows, facet counts, PII, tenant data, raw query results, embeddings, or dashboard extracts. **Hidden risk:** the tool run leaks data or persists unsafe output while trying to prove safety. **Required professional action:** classify tool permission/sandbox, prefer read-only or dry-run execution, redact or aggregate output, and record retention limits. **Route to:** `agent-tool-permission-sandbox`, `security-privacy-gate`, and this capability. **Evidence required:** command/action class, permission state, sandbox boundary, redaction rule, artifact path, and output retention decision.

# Critical Details

- **Permission filtering in search engines is easy to forget and hard to audit.** A multi-tenant application that stores all tenant documents in a shared Elasticsearch index must include `{ "term": { "tenant_id": "current-tenant" } }` (or equivalent document-level security) in every query. A developer who forgets the filter during a new query implementation silently exposes all tenants' data. The permission filter must be in a shared query builder that cannot be bypassed.
- **Analyzer changes are breaking schema changes.** Changing the analyzer for a field (e.g., from `standard` to `english` stemmer) changes how tokens are stored. Documents indexed before the change are stored with the old tokens; new queries use the new token format — relevance breaks silently. The only fix is a full reindex. Treat analyzer changes as schema migrations requiring the same review discipline as database DDL changes.
- **Reindex does not satisfy GDPR Right to Erasure in real time.** If a user requests deletion and the next scheduled reindex is in 6 hours, the deleted user's data remains discoverable via search for 6 hours. For products with GDPR obligations, real-time deletion (tombstone document, update by query, or partial update to null sensitive fields) must be implemented alongside the scheduled reindex path.
- **Search results that affect eligibility, pricing, or inventory must enforce freshness.** A search for "available products" that can return out-of-stock items due to ingestion lag is a product defect. A search for "eligible users" that can return ineligible users due to lag is a compliance defect. For safety-critical freshness, either use the source-of-truth directly for the eligibility check, or add a real-time source-of-truth verification after the search returns candidates.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 selection, boundary, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete search/analytics design, when engine justification or permission/freshness coverage is uncertain, or before implementation planning depends on the design. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when engine selection, relevance/metric validation, ingestion/deletion patterns, drift/reconciliation, or graph/memory/trajectory reuse needs depth. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

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

- **Cross-tenant disclosure:** Multi-tenant search returns cross-tenant results because one query path omits the shared tenant and permission filter; the incident is discovered only during audit. Every query builder or engine-level security rule must have allowed, denied, wrong-tenant, private, deleted, and support/admin validation.
- **Analyzer migration drift:** Analyzer changed in place; BM25 relevance degraded for 60% of queries; old and new token vintages coexist and no alert fires until user complaints. Analyzer and mapping changes need versioned index rebuild, relevance comparison, and rollback alias evidence.
- **Reindex outage:** Reindex takes 4 hours; search endpoint returns stale or empty results; there is no blue-green index strategy, retained old index, or cutover rollback. Reindex work must preserve serving path, validate old/new count and relevance deltas, and define cleanup owner.
- **Erasure failure:** GDPR deletion is not applied to the search index; deleted user data remains discoverable 3 days later. Periodic rebuild is not deletion proof when PII or visibility changes require real-time tombstone/update propagation.
- **Silent ingestion drift:** Ingestion pipeline failure silently drops 12% of documents; drift is not detected; product shows fewer results than exist. Source-to-derived counts, checksums, sampled documents, failed-write alerts, and backfill owner are required.
- **Metric inflation:** Analytics dashboard double-counts events due to at-least-once delivery without deduplication; revenue report is inflated by 8%. Metric definitions need grain, dedupe key, late-arrival policy, reconciliation query, and dashboard freshness evidence.
- **Facet count leak:** Facet counts are computed globally before permission filtering; hidden categories or tenant record volumes are disclosed even though result rows are filtered. Counts and aggregations must be permission-scoped, not only documents.
- **Stale-memory reuse:** Project memory says an index contains `visibility`, but current generated schema renamed it to `access_scope`; a copied design silently drops the filter. Memory and graph evidence must be current-source confirmed or downgraded to residual risk.
- **Unsafe validation export:** A support command exports raw dashboard rows or embeddings into a report to debug metric drift; the report persists restricted data beyond its intended audience. Tool permission, redaction, aggregation, and retention boundaries are part of the design evidence.
- **Fallback correctness gap:** Search outage fallback reads from the source database but omits relevance ordering, permission parity, or stale-data signal; users see inconsistent or unauthorized results during degradation. Fallback behavior must preserve security and clearly state reduced functionality.

# Output Contract

Return a search or analytics design with:

- `mode_selected` (search engine justification / analytics engine justification / schema or query change / ingestion and freshness / permission privacy deletion)
- `design_scope` (product query, user or decision maker, source surfaces, excluded relational/cache/source-model alternatives, and release boundary)
- `source_evidence` (current source-of-truth schema, queries, repository graph, project memory, execution trajectory, telemetry, dashboards, ingestion jobs, and freshness limits)
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
- `relevance_or_metric_validation` (sample queries, judgment set, metric definition, dedupe rule, reconciliation query, or dashboard validator)
- `changed_design_to_validation_map` (each engine/schema/query/ingestion/freshness/permission/erasure decision mapped to test, validator, monitoring, or residual risk)
- `validation_commands` (search relevance, permission, freshness, drift, metric, reindex, dashboard, generated-artifact, owner-review, or manual procedure; validator/tool; artifact/report path; output/exit code or manual result; changed design scope; freshness after final edit)
- `tool_permission_sandbox_record` (for commands/connectors/exports that can reveal data: action class, permission state, sandbox or read-only boundary, redaction/aggregation rule, artifact retention, rollback/revert path, and unsupported evidence limits)
- `handoff_boundaries` (what belongs to relational indexing, cache, data model, migration, security/privacy, reliability, release, or acceptance gates)
- `reuse_and_freshness_judgment` (accepted/rejected graph, memory, or execution-trajectory evidence and why)
- `evidence_limits` (what was not verified: production data distribution, live index mapping, real user relevance, dashboard consumers, erasure SLA, or pipeline lag)

# Evidence Contract

Close a search-analytics-design change only when the output names selected mode, design scope, current source evidence inspected, engine justification versus simpler alternatives, source-of-truth and derived-view boundary, permission/erasure contract, freshness SLO, reindex/backfill/rollback path, drift/reconciliation plan, relevance or metric validation, graph/memory/execution reuse judgment, changed-design-to-validation map, handoff boundaries, residual risk, and evidence limits. A design that only names an engine, index, or dashboard is not sufficient evidence.

Validation evidence must name command or review procedure, validator/tool, artifact/report path, output and exit code or manual result, changed design scope, and freshness after the final schema/query/ingestion/metric/generated-artifact edit. State boundaries inspected, what evidence proves, what evidence does not prove, reuse and placement rationale for graph/memory/trajectory claims, behavior preservation for existing queries/dashboards/consumers, residual risk, and next gate or handoff owner. A relevance sample proves only the sampled query set; a reconciliation query proves only the selected grain and date range; a dashboard screenshot proves display state, not source correctness.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak designs usually choose an engine before proving need, omit source-of-truth boundaries, assume UI-side permission filtering, treat reindex as a maintenance task with downtime, use "eventually consistent" without SLO, skip erasure/tombstone behavior, or publish analytics without reconciliation. Improved outputs must name mode, source evidence, derived-view contract, permission/freshness/drift/reindex controls, validation mapping, and handoff boundaries while keeping detailed engine examples in references.

# Routing Coverage

Route here when the primary work is full-text relevance, faceted search, semantic/vector retrieval, OLAP aggregation, analytical read models, event analytics, search/analytics schema evolution, ingestion freshness, drift, reindex/backfill, or derived-data permission and erasure behavior. Guard against over-routing by handing off when the primary concern is SQL query/index tuning (`indexing-query-optimization`), cache-only acceleration (`cache-design`), conceptual domain source modeling (`data-model-design`), NoSQL key/document design (`nosql-database`), migration execution sequencing (`data-migration-design`), security/privacy approval (`security-privacy-gate`), reliability SLO/alert operation (`reliability-observability-gate`), or release cutover (`delivery-release-gate`).

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
11. Selected mode, design scope, source evidence, and simpler alternatives rejected are explicit.
12. Repository graph, project memory, and execution trajectory evidence are current-source confirmed or marked not verified.
13. Relevance or metric validation is defined with sample queries, judgment set, reconciliation query, or dashboard validator.
14. Every changed engine, schema, query, ingestion, freshness, permission, erasure, and fallback decision maps to validation evidence or named residual risk.
15. Handoff boundaries and evidence limits are explicit so the design is not over-claimed as relational indexing proof, security approval, live production performance, release approval, or metric correctness certification.
16. Validation commands or manual review procedures record validator/tool, report or artifact, output and exit code or manual result, changed scope, freshness, what evidence proves, and what evidence does not prove.
17. Tool permission/sandbox evidence exists when validation, debugging, support export, reindex, backfill, connector, warehouse, search-admin, or dashboard actions can expose restricted data or mutate derived systems.

# Used By

- data-middleware-change-builder
- experience-impact-modeler

# Handoff

Hand off to `indexing-query-optimization` when the relational database can be tuned to serve the query; `data-migration-design` for reindex or backfill work planning; `security-privacy-gate` for permission and GDPR compliance review; `reliability-observability-gate` for freshness SLO and drift alert design; `delivery-release-gate` for reindex deployment coordination.

# Completion Criteria

The capability is complete when **the search or analytics design is justified, the permission model is enforced in every query path, freshness is product-approved with a measurable SLO, reindex is zero-downtime, GDPR erasure is real-time for PII, and drift is detectable before it affects product quality**.
