---
name: nosql-database
description: Selects NoSQL storage only when access patterns, schema flexibility, scale model, and consistency boundaries justify it.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "46"
changeforge_version: 0.1.0
---

# Mission

**Decide and design NoSQL database changes only when access patterns, data shape, scale model, and consistency boundaries make non-relational storage the safer production choice** - ensuring partition keys, consistency guarantees, denormalization ownership, schema versioning, capacity limits, and operational validation are explicit before any non-relational store enters production.

# When To Use

Use this capability when a change proposes document, key-value, wide-column, graph, time-series, or other non-relational storage; adds indexes, collections, partitions, table layouts, item schemas, or document validators to an existing NoSQL store; changes partition/sort key design, consistency level, TTL, schema version, or denormalized copies; introduces access-pattern-specific projections; or is flagged in review for "hot partition", "unbounded document growth", "missing schema validation", "cross-partition transaction", or "NoSQL because it scales".

# Do Not Use When

Do not use this capability to avoid relational modeling, constraints, referential integrity, or JOIN-based queries when product invariants require them. Do not use it to justify NoSQL because "it is more modern" or "it scales better" without concrete access-pattern and production-volume evidence. Do not use it as a cache design when the store is only an acceleration layer, or as search/analytics design when full-text relevance, faceting, or OLAP is primary.

# Stage Fit

- **Planning / design:** choose the store role, access patterns, key/index layout, consistency boundaries, schemaVersion policy, TTL/retention, capacity budget, and rejected relational/cache/search alternatives before implementation.
- **Coding / implementation:** update collection/table definitions, validators, indexes, partition keys, write/read repositories, migration/backfill scripts, denormalized writers, and observability together.
- **Bug-fix / debugging / repair:** reproduce hot partition, stale read, item overflow, shape drift, TTL deletion, cross-partition partial write, or denormalization drift before changing the physical model.
- **Code-review / refactoring:** reject NoSQL changes that lack access-pattern evidence, cardinality/skew proof, consistency contract, reader compatibility, source-of-truth ownership, graph/memory freshness, and behavior preservation.
- **Testing / release / handoff:** verify access-pattern tests, old/new schema reads, capacity/cost checks, drift repair, migration/backfill validation, rollback behavior, evidence freshness, and data/security/reliability handoff before release.

# Non-Negotiable Rules

- **Define access patterns before choosing keys.** NoSQL key design is hard to reverse in most stores. Partition keys, sort keys, secondary indexes, document embedding, and clustering columns must be derived from named read/write patterns, not from entity diagrams alone.
- **State the consistency model and which invariants are eventually consistent.** Every invariant that must be correct (balance, inventory, lock, permission, entitlement, audit) must identify strong/eventual consistency, stale-read behavior, and user-visible consequence.
- **Avoid cross-item or cross-partition transactions unless explicitly supported.** If a business invariant requires atomically updating records across partitions or stores, the design must use supported transactions, Saga, Outbox, compensation, or a relational model instead of assuming atomicity.
- **Partition keys must be high-cardinality and workload-balanced.** Low-cardinality keys such as `status`, `type`, or a single large tenant create hot partitions. Any tenant, time, status, or category key must include a distribution strategy and production load estimate.
- **Denormalized data requires explicit ownership and repair.** Every duplicated field names its source of truth, propagation mechanism, accepted staleness, drift detection, and repair path.
- **Schema versioning is mandatory for documents/items with evolving shape.** Every document type needs a version field or equivalent; readers must handle old versions safely; migrations/backfills must be planned when new required fields appear.
- **Store limits, quotas, and cost ceilings are design inputs.** Item/document size, partition size, index count, throughput, read/write unit cost, TTL/retention, and operational alerts must be checked against projected data volume before production.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Store selection | New NoSQL proposal, replacement of relational store, or new read model/projection. | Prove non-relational storage is the right source or derived store for named workload. | Access patterns, invariants, data shape, scale model, relational/cache/search alternatives rejected. | `data-model-design`, `relational-database`, `search-analytics-design` | "NoSQL scales better" as rationale. |
| Key and partition design | New table/collection, partition key, sort key, clustering key, shard key, or secondary index. | Prevent hot partitions and unsupported queries before data exists. | Query list, key schema, cardinality, item size, index projections, tenant/time distribution. | `indexing-query-optimization`, `performance-budgeting` | Key choice from entity name alone. |
| Consistency and transaction boundary | Strong/eventual read choice, cross-item update, denormalized write, saga/outbox, or stale-read tolerance. | Name invariants and design safe consistency behavior. | Invariant map, consistency level, stale-read consequence, atomicity support, compensation/reconciliation. | `transaction-consistency`, `idempotency-retry-design`, `domain-event-modeling` | Cross-partition assumptions. |
| Schema evolution and migration | New required field, schemaVersion change, backfill, TTL change, re-shard, table split, or projection rebuild. | Keep old data, old code, new code, and rollback coherent. | Version policy, reader compatibility, backfill plan, dual-read/write, validation query, rollback behavior. | `data-migration-design`, `version-compatibility`, `delivery-release-gate` | In-place shape change with no old-document handling. |
| Denormalized read model | Duplicated fields, materialized documents, event-fed projections, or read optimization. | Make duplication owned, repairable, and bounded by staleness. | Source of truth, propagation trigger, lag budget, drift check, replay/repair path, consumer impact. | `data-side-effect-flow-tracing`, `observability`, `quality-test-gate` | Silent dual writes. |
| Operational readiness review | Production NoSQL change, capacity/cost concern, throttle, hot key, large tenant, or quota alert. | Prove the design can run under expected volume and failure modes. | Capacity math, service quotas, cost budget, throttle behavior, alarms, load/smoke validation. | `reliability-observability-gate`, `performance-budgeting`, `backup-recovery` | Dev-data-only confidence. |

# Industry Benchmarks

Anchor against DynamoDB access-pattern-first modeling, MongoDB document validation and anti-patterns, Cassandra wide-column partition modeling, Firestore/Bigtable query limits, Redis key/value TTL discipline, graph database traversal modeling, time-series cardinality and retention design, CAP/PACELC tradeoffs, and Kleppmann/Fowler/Sadalage aggregate-oriented data modeling. Keep this body focused on selection and evidence rules; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for store-selection matrices, DynamoDB access-pattern templates, consistency matrices, operational-limit checks, and anti-pattern review.

# Selection Rules

Select this capability when a non-relational store is being proposed or its physical schema, key design, partitioning, indexing, consistency behavior, TTL, denormalization, or operational limits are the primary decision. Prefer `relational-database` when constraints, joins, referential integrity, or ACID multi-table transactions are required. Prefer `cache-design` when the store is only an acceleration layer. Prefer `search-analytics-design` for full-text relevance, faceting, or OLAP. Prefer `data-model-design` when domain entities and invariants are not yet understood. Prefer `data-migration-design` when existing stored data must be moved, backfilled, or reshaped.

# Risk Escalation Rules

Escalate when NoSQL is proposed for financial records, ledger data, permissions, inventory, entitlements, audit records, regulated data, or any invariant requiring atomic multi-entity updates; a partition key has low cardinality or a tenant/time/status hotspot; projected data approaches item/document/partition/index/service quota limits; cross-partition transactions are assumed without database support; denormalized data lacks authoritative writer or drift detection; or schema evolution affects existing stored records without reader compatibility and backfill validation.

# Proactive Professional Triggers

- **Signal:** A NoSQL table or collection is designed from entity shape without listing access patterns.
  **Hidden risk:** keys cannot serve required queries without scans, backfills, duplicate projections, or wrong store selection.
  **Required professional action:** require and document an access-pattern inventory, compare relational/cache/search alternatives, and verify each accepted key/index against a caller query.
  **Route to:** `nosql-database`, `repository-context-map`.
  **Evidence required:** AP list, query shape, key/index map, rejected scan-based design, command/report path, and residual query risk.
- **Signal:** A partition, shard, or GSI key uses status, type, tenant, category, or date alone.
  **Hidden risk:** hot partition, unbounded item collection, hidden write amplification, or throttle collapse appears only under production skew.
  **Required professional action:** inspect and compare cardinality, top-tenant/time skew, write rate, distribution strategy, alternate access path, and monitoring.
  **Route to:** `performance-budgeting`, `reliability-observability-gate`.
  **Evidence required:** cardinality report, skew estimate, write-rate math, throttle limit, monitoring/alert plan, and residual capacity risk.
- **Signal:** A document shape gains a required field without schema versioning.
  **Hidden risk:** old documents break readers after deploy, mixed-version code corrupts data, or rollback cannot read newly shaped records.
  **Required professional action:** require schemaVersion, backward-compatible reader/upcaster, migration or backfill plan, validation query, and rollback behavior.
  **Route to:** `data-migration-design`, `version-compatibility`.
  **Evidence required:** version map, old/new reader test, validation query output, rollback plan, and stale-document residual risk.
- **Signal:** Denormalized fields are copied across items or collections.
  **Hidden risk:** source-of-truth drift, stale reads, replay gaps, or silent dual-write loss breaks product invariants.
  **Required professional action:** model writer authority, propagation trigger, accepted lag, drift detection, replay/repair path, and consumer impact.
  **Route to:** `data-side-effect-flow-tracing`, `domain-event-modeling`.
  **Evidence required:** writer owner, event/outbox/replay path, reconciliation check, drift metric, repair command, and residual staleness owner.
- **Signal:** Prior project memory says a NoSQL pattern worked elsewhere.
  **Hidden risk:** stale pattern ignores current access patterns, tenant skew, store version, limits, consistency invariants, or execution trajectory.
  **Required professional action:** inspect and verify current source, repository graph, workload volume, store version, tests, telemetry, and validation freshness before reuse.
  **Route to:** `project-memory-governance`, `repository-graph-analysis`.
  **Evidence required:** inspected current paths, accepted/rejected memory, command/report timestamp, freshness limits, graph boundary, and residual risk.

# Critical Details

- **NoSQL is an access-pattern commitment.** The design should start from AP1..N and only then choose store, key, indexes, and document embedding.
- **"Schemaless" is not "versionless."** Flexible document stores move schema enforcement into application readers, validators, and migrations; they do not remove schema governance.
- **Eventual consistency needs a product contract.** If a stale read can expose permissions, oversell inventory, misstate a balance, or hide an audit record, the design needs strong reads, source-of-truth verification, or a different store.
- **Derived NoSQL projections are not source of truth unless explicitly designed as such.** If a projection can be rebuilt from events or relational data, call it derived, name lag tolerance, and define rebuild/drift detection.
- **Operational limits fail abruptly.** Item size, partition size, index projection size, service quotas, and TTL/backfill behavior need validation before data growth makes redesign expensive.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 NoSQL routing, ownership, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete NoSQL design. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when store selection, access-pattern templates, consistency matrices, operational limits, or anti-pattern detail is needed. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| DynamoDB PK = `status` | Low-cardinality hot partition; writes throttle on popular status | Use entity or tenant+entity key; put status lookup behind carefully scoped GSI or projection |
| MongoDB document with no `schemaVersion` | Required field change breaks old documents at read time | Add version field; readers upcast or branch safely; backfill old documents |
| Cassandra `ALLOW FILTERING` in production | Cluster scan; latency grows with data volume | Redesign partition/clustering key or build a query-specific table |
| Item stores unbounded event array | Item/document grows until hard limit; writes fail abruptly | Segment by time or event id; use append-only child items or object storage reference |
| Redis used as durable source of truth for sessions/orders | Eviction or crash loses authoritative state | Use Redis as cache/ephemeral store only, or choose a durable store with recovery plan |
| Denormalized field copied with no propagation | Source updates do not reach copies; stale data persists indefinitely | Define event/outbox propagation, accepted lag, reconciliation, and repair |

# Failure Modes

- **Hot partition:** one tenant, status, or time bucket receives most writes and exhausts partition throughput.
- **Shape drift:** years of schema-free writes produce incompatible document variants and branching readers.
- **Item overflow:** unbounded list/map grows past item or document size limit and write path fails.
- **Cross-partition partial write:** one update succeeds and the matching invariant update fails, leaving inconsistent business state.
- **Stale read:** eventually consistent secondary index hides a just-written permission, inventory, or lock change.
- **TTL mistake:** ephemeral counters or sessions never expire, or required records expire because TTL field semantics were not documented.
- **Denormalization drift:** projected fields diverge from their authoritative source and no reconciliation detects it.
- **Rollback-incompatible shape:** new code writes a required field or index format that old code cannot read after rollback.

# Output Contract

Return a NoSQL design with:

- `mode_selected` (store selection, key/partition design, consistency boundary, schema evolution, denormalized read model, or operational readiness)
- `source_evidence` (current data model, access paths, repository graph, project memory, workload estimates, store version, docs/tests/telemetry inspected with freshness limits)
- `store_selection` (store type/version; source-of-truth vs derived-store role; rejected relational/cache/search alternatives)
- `access_patterns` (AP1..N; query type, filters, sort/range, result shape, consistency need, expected volume, caller)
- `write_patterns` (write rate, burst/skew, tenant/time distribution, append/update/delete behavior)
- `key_schema` (partition/shard key, sort/clustering key, secondary indexes, projection fields, cardinality and hotspot rationale)
- `item_or_document_schema` (fields, types, `schemaVersion`, validators, TTL/retention attributes, max projected item/document size)
- `consistency_model` (per invariant: strong/eventual, stale-read consequence, read/write settings, conflict handling)
- `transaction_and_atomicity` (single-item, multi-item, cross-partition, saga/outbox/compensation, unsupported assumptions rejected)
- `denormalization_rules` (duplicated fields, authoritative source, propagation trigger, accepted lag, drift detection, repair/replay)
- `schema_versioning_and_migration` (reader compatibility, backfill/dual-write, validation query, rollback behavior)
- `capacity_and_operational_limits` (item/document/partition/index/throughput/quota/cost limits with projected volume)
- `security_and_retention` (PII/PHI/PAN classification if present, encryption/access logging, TTL, retention, erasure path)
- `observability` (latency, throttling, hot partition, item size, index lag, drift, quota, and cost signals)
- `test_strategy` (access-pattern tests, stale-read handling, hot partition simulation, TTL expiration, schema-version compatibility, drift repair)
- `graph_and_memory_decisions` (current writers/readers/consumers confirmed, reused patterns accepted or rejected, stale memory caveats)
- `changed_store_to_validation_map` (each key/index/schema/TTL/consistency/denormalization/migration decision mapped to validator/test/monitoring or residual risk)
- `handoff_boundaries` (what belongs to data model, relational DB, indexing, cache, search, migration, transaction, security, reliability, or release work)
- `evidence_limits` (uninspected production data, quotas, traffic skew, cloud account settings, telemetry, migrations, or live performance)

# Evidence Contract

- **Repository evidence:** name data models, repositories, collection/table definitions, indexes, migration/backfill scripts, tests, docs, and registry entries inspected; if no implementation exists, state that output is a design contract rather than verified source behavior.
- **Access-pattern evidence:** every key/index exists because a named caller and query needs it; every rejected access path states why scan, join, cache, search, or relational design was not chosen.
- **Graph and memory evidence:** repository graph and project memory can suggest candidate writers/readers, but current source, tests, telemetry, and store constraints must confirm them before reuse.
- **Execution evidence:** map NoSQL decisions to validators, tests, load/capacity checks, migration dry runs, schema-version compatibility checks, monitoring, or explicit not-verified residual risk.
- **Boundary evidence:** distinguish source-of-truth data, derived projections, caches, search indexes, and migration artifacts so the NoSQL design is not over-claimed as conceptual model, cache policy, search relevance, or release approval.

Validation evidence must name boundaries inspected, command or manual-review procedure, validator, artifact/report path, exit code or manual result, inspected output, store/version scope, owner, and freshness after the final table, collection, key, index, schemaVersion, TTL, denormalization, or migration edit. State what evidence proves, what evidence does not prove, reuse and placement rationale for graph/memory/execution claims, behavior preservation for existing readers/writers/backfills/rollbacks, residual risk, and next gate or handoff owner. Repository graph proves only current code topology; project memory proves only prior context; local access-pattern tests do not prove live cardinality, tenant skew, cloud quota, cost, or production latency unless those validators ran.

# Benchmark Coverage

Professional NoSQL design covers access-pattern completeness, store fit, source-of-truth role, key cardinality, hot-partition resistance, consistency and atomicity, denormalization ownership, schema versioning, TTL/retention, capacity and cost limits, security/retention classification, observability, graph/memory freshness, and validation mapping. A key-value or document shape without production access-pattern and consistency evidence is incomplete.

# Routing Coverage

Route here when the primary question is non-relational store selection, physical document/item/table design, partition/shard key choice, secondary index layout, denormalized projection ownership, schema versioning, TTL, or NoSQL operational limits. Hand off to `data-model-design` for conceptual domain shape, `relational-database` for SQL constraints/joins/ACID design, `indexing-query-optimization` for relational query plans, `cache-design` for acceleration-only stores, `search-analytics-design` for search/OLAP engines, `transaction-consistency` for invariant/atomicity depth, `data-migration-design` for live backfill/cutover sequencing, `security-privacy-gate` for regulated data, and `reliability-observability-gate` for capacity/cost/SLO readiness.

# Quality Gate

The design is complete only when:

1. Every access pattern is listed and maps to a key, index, query, or rejected alternative.
2. NoSQL choice is justified against relational, cache, search, and existing-store alternatives.
3. Partition/shard keys have sufficient cardinality and documented skew/hotspot mitigation.
4. Consistency model is explicit for every invariant that must be correct.
5. Cross-partition or cross-item transactions either use supported database features or have Saga/Outbox/compensation design.
6. Every evolving document/item type carries schema versioning and reader backward compatibility.
7. TTL and retention are defined for ephemeral data, regulated data, and derived projections.
8. Projected item/document/partition/index size and service quota limits are validated against production estimates.
9. Denormalization ownership, propagation, drift detection, and repair are explicit.
10. Observability covers latency, throttling, hot partitions, item/document size, index lag, drift, quota, and cost.
11. Selected mode, source evidence, source-of-truth role, access-pattern map, and handoff boundaries are explicit.
12. Repository graph, project memory, and prior execution trajectory evidence are confirmed against current source or marked stale/not verified.
13. Every changed key, index, schemaVersion, TTL, consistency, denormalization, migration, and retention decision maps to validation evidence or named residual risk.
14. Evidence limits are stated so the design is not over-claimed as live performance, production cardinality, security certification, migration execution, or release approval.
15. Validation records include command/tool or manual-review procedure, artifact or report path, exit code or manual result, inspected output, changed store scope, owner, freshness after final edit, what the evidence proves, and what it cannot prove.

# Used By

- data-middleware-change-builder

# Handoff

Hand off to `data-model-design` when domain entities, invariants, or ownership are unresolved; `relational-database` when constraints, joins, or ACID multi-table transactions are required; `indexing-query-optimization` when the primary issue is relational query/index tuning; `transaction-consistency` for Saga, Outbox, or cross-item atomicity; `cache-design` when the store is only an acceleration layer; `search-analytics-design` for full-text/faceted/OLAP engines; `data-migration-design` and `version-compatibility` for backfill, schema evolution, or mixed-version rollout; `security-privacy-gate` for regulated or tenant-sensitive data; and `reliability-observability-gate` for capacity, SLO, cost, or operational readiness.

# Completion Criteria

The capability is complete when **NoSQL use is justified by concrete access patterns, the selected store role is explicit, partition/key/index design supports required reads and writes without hidden hotspot risk, consistency is named per invariant, schema versioning protects old data, operational limits are validated, denormalization has an authoritative writer plus repair path, and every material decision maps to evidence or residual risk**.
