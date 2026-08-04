# Search Analytics Design Evidence Patterns

Use this reference when search or analytics closure depends on validation freshness, prior source or task evidence claims, permission/freshness/reindex proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second engine-selection guide.

## Search-Analytics-To-Validation Map

| Search or analytics claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Engine use is justified | Product query, source/read-model evidence, relevance/facet/OLAP need, rejected relational/cache alternatives, and owner review | The inspected need has a reason to use a derived engine | Future data volume, relevance quality, or operational cost is safe |
| Derived-view boundary is explicit | Source of truth, write path, indexed fields, generated/query consumers, and no-write-first rule | Inspected engine is not treated as authoritative source | Uninspected dashboards, support tools, and exports remain outside the claim |
| Permission and erasure are enforced | Tenant/role/visibility filter contract, shared query builder or engine security, tombstone/delete path, and denied/deleted evidence | Inspected query/index design addresses obvious disclosure risk | Certification and uninspected support or admin paths remain separate decisions |
| Freshness is measurable | Product freshness objective and consequence, ingestion path, source/query-visible timestamps, lag and drift metrics, stale behavior, and recovery owner | Inspected derived data has a freshness contract | Production outages, unseen backlog shapes, and regional lag remain unproven |
| Reindex/backfill is reversible | Old/new schema, selected in-place or versioned cutover, validation comparison, containment or rollback condition, and cleanup owner | Inspected schema or mapping change has a safe migration shape | Live duration, capacity pressure, and undiscovered consumer compatibility remain unproven |
| Relevance or metric is validated | Sample queries/judgment set, metric grain, dedupe key, reconciliation query, dashboard validator, or residual risk | Inspected result quality or metric semantics are checked for named cases | Live user satisfaction, emerging queries, and uninspected analytical consumers remain unproven |
| Tool output is safe to retain | Action class, permission state, redaction/aggregation rule, artifact path, retention owner, and rollback/revert path | Inspected proof collection avoids obvious data leakage | Uninspected connectors, exports, and future debug output remain outside the claim |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, generated clients, dashboards, telemetry, support signals, and prior validation as selectors until current schemas, queries, ingestion jobs, tests, and owner evidence confirm them.
- Recheck prior "index has field", "metric is reconciled", "permission filter is global", or "freshness objective is met" claims against current source, generated artifacts, dashboards, and validation.
- Mark evidence stale after edits to indexed fields, analyzers, query builders, permissions, ingestion jobs, freshness objectives, metrics, dashboards, reindex scripts, generated clients, tests, reports, or build outputs.
- Map each changed search or analytics decision to a command, query, dashboard, report, owner review, or explicit not-run residual risk. Material decisions include engine, schema, query, ingestion, freshness, permission, erasure, fallback, metric or relevance, tool output, and handoff.

- If live reindex, backfill, warehouse export, support search, dashboard mutation, or connector write, record environment, owner approval, stop condition, rollback or containment path, and redaction rule.
- If production search/admin query, telemetry, warehouse, or dashboard export, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/PII/secret-bearing fields.
