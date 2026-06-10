---
name: data-middleware-change-builder
description: Guides changes to SQL, NoSQL, cache, queue, search, object storage, and middleware layers, focusing on source of truth, consistency, indexes, query performance, invalidation, delivery semantics, and failure modes.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Data Middleware Change Builder

## Mission
Design and review changes to persistence, caching, queueing, search, streaming, and middleware layers with explicit source-of-truth ownership, consistency model, access pattern–driven index design, cache invalidation correctness, queue delivery semantics, and deterministic failure recovery — because data layer bugs are the most expensive to reverse and the least visible until they corrupt production.

## When To Use
- Database schema changes, query rewrites, index additions, or constraint modifications in SQL or NoSQL stores.
- Cache layer additions, key design changes, TTL modifications, or invalidation logic changes.
- Message queue or event stream additions, consumer logic changes, retry behavior, or DLQ routing.
- Search index mapping changes, re-indexing strategies, or relevance pipeline modifications.
- Object storage lifecycle, access pattern, or retention policy changes.
- Stream processing topology changes, windowing logic, or aggregation state changes.
- Replication, sharding, or multi-region consistency configuration changes.
- Middleware configuration changes that affect data durability, ordering, or delivery guarantees.

## Do Not Use When
- API response shape or DTO design is the primary concern — use `data-api-contract-changer` for contract work.
- Frontend state management or client caching is the only concern — use `frontend-change-builder`.
- Infrastructure provisioning (adding a new Redis cluster) without any behavior change — use `delivery-release-gate` for infrastructure rollout.

## Non-Negotiable Rules
- **Declare the source of truth before any read or write path is designed** — every entity has exactly one authoritative store; all other stores are derived.
- **Design indexes from access patterns, not from data shape** — an index that matches no query plan is pure write overhead; a missing index on a query run 10,000 times per second is a production incident.
- **Cache invalidation must be explicit** — stale-reads-on-write and cache stampede are not edge cases; they are the default failure mode of cache-first designs.
- **Queue delivery semantics must be declared**: exactly-once, at-least-once, or at-most-once — and the application must be designed to handle the declared semantics correctly.
- **Poison message handling is mandatory**: every queue consumer must route unprocessable messages to a dead-letter queue (DLQ) with metadata — not silently skip or crash-loop.
- **Replication lag is a first-class design constraint** — never read from a replica for operations where stale data causes incorrect behavior (balance check before debit, duplicate prevention, authorization).
- **Never write a forward migration without a tested rollback migration** — data layer rollbacks that require manual intervention are the leading cause of extended production outages.
- **Large table operations must use online migration strategies** — offline migrations that require downtime on tables > 100k rows are not acceptable in production without a formal maintenance window.
- **Search re-indexing must be blue/green or shadow-indexed** — cutover to a new mapping during active traffic corrupts relevance scores and may drop documents.

## Industry Benchmarks
- **Use-the-Index-Luke (Markus Winand)**: Index design starting from query requirements — no index without a named query it serves; no query without explaining its index strategy.
- **Google SRE Book (Chapter 26: Data Integrity)**: Data integrity requires defense in depth — application-level, storage-level, backup-level, and audit-level verification.
- **Redis Documentation — Cache-Aside vs. Write-Through vs. Write-Behind**: Each cache strategy has distinct consistency and failure mode properties; the strategy must be declared and designed for.
- **AWS Well-Architected Framework — Data Layer**: Separate read and write paths; design for scale from day one; understand and document consistency trade-offs.
- **CAP Theorem / PACELC**: When partitions occur, choose between Consistency and Availability explicitly. Document the choice and its business consequences.
- **Kafka Design Guide (Confluent)**: Partition key design determines ordering guarantees; consumer group design determines parallelism; offset management determines exactly-once vs. at-least-once.
- **Elasticsearch Index Lifecycle Management (ILM)**: Time-based index rollover, hot/warm/cold tier management, and delete phases — required for high-volume log and event indices.
- **PostgreSQL EXPLAIN ANALYZE**: Every non-trivial query change must be validated with `EXPLAIN (ANALYZE, BUFFERS)` against realistic data volume before deployment.

### Technology Selection Matrix

| Workload | Preferred Technology | Key Design Constraints |
|---|---|---|
| Relational transactions | PostgreSQL / MySQL | ACID, isolation level, index design |
| Document store | MongoDB / DynamoDB | Denormalization, partition key, consistency model |
| Key-value cache | Redis / Memcached | TTL, eviction policy, cache-aside vs. write-through |
| Full-text search | Elasticsearch / OpenSearch | Mapping, analyzer, ILM, re-index strategy |
| Message queue | RabbitMQ / SQS | Delivery semantics, DLQ, visibility timeout |
| Event streaming | Kafka / Kinesis | Partition key, consumer groups, offset commit |
| Object storage | S3 / GCS | Versioning, lifecycle, access control, consistency |
| Time series | TimescaleDB / InfluxDB | Retention policy, aggregation, compression |

## Technical Selection Criteria
Evaluate every data or middleware change against:
- **Source of truth declaration**: Which store is authoritative? Which stores are derived or cached?
- **Consistency model**: Strong, eventual, causal, read-your-writes — and which operations require strong consistency?
- **Access pattern analysis**: What queries drive read load? Write load? What are the access frequency, cardinality, and filter/sort combinations?
- **Index strategy**: Which existing indexes are affected? Are new indexes justified by specific named queries? Are write overheads acceptable?
- **Query plan validation**: Has `EXPLAIN ANALYZE` been run against realistic data volumes for all modified queries?
- **Cache key design**: Is the cache key unique enough to prevent cross-tenant collision? Is the TTL appropriate for staleness tolerance?
- **Cache invalidation strategy**: How is the cache invalidated on write? Stale-on-write, TTL expiry, explicit invalidation, or write-through?
- **Queue delivery semantics**: At-least-once, exactly-once, or at-most-once — and is the consumer designed to handle duplicate messages?
- **Poison message routing**: What happens when a message cannot be processed? Is there a DLQ with alerting?
- **Replication lag tolerance**: Are there read operations that must see the latest write? Are they using the primary or a replica?
- **Migration rollback**: Is there a tested rollback migration? Can the old application code function with the new schema?

## Mode Matrix
Select the data/middleware mode before changing storage, cache, queue, search, backfill, or query behavior.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| New store or access path | New table, collection, cache key, queue topic, search index, object path, or query. | Source of truth, consistency, access pattern, index/cache/queue/search design, observability. | Owner store, access patterns, query plan or capacity estimate, test/rollback plan. | `relational-database`, `cache-design`, `message-queue-design`, `search-analytics-design` | Multi-store sync unless required. |
| Modify existing query/index/cache | Query, index, TTL, invalidation, key namespace, or read path changes. | Preserve correctness while proving plan, staleness, tenant isolation, and write overhead. | EXPLAIN/plan, cache invalidation path, affected callers, before/after latency. | `indexing-query-optimization`, `cache-design`, `quality-test-gate` | Speculative indexes or TTL-only mutable cache. |
| Bug fix / data inconsistency | Drift, stale cache, duplicate messages, missed events, search gap, bad migration. | Verify source of truth, repair pattern, same-pattern scan, regression proof. | Data sample, root cause, impacted scope, repair/backfill plan, tests. | `failure-diagnosis`, `agent-execution-discipline`, `regression-testing` | Manual data repair without owner/rollback. |
| Queue/stream reliability | Kafka/queue offset, retry, ordering, DLQ, replay, lag, or idempotency changes. | Delivery semantics, idempotent consumer, offset commit boundary, replay and observability. | ack/commit point, retry/DLQ config, replay test, lag metrics. | `message-queue-design`, `idempotency-retry-design`, `reliability-observability-gate` | Exactly-once claims without proof. |
| Migration/backfill/freshness | Migration, backfill, reindex, replay, data freshness, retention, or source-of-truth shift. | Online safety, rollback, throttling, freshness SLA, reconciliation. | Forward/rollback test, batch size, progress metric, cutover/reconcile plan. | `data-migration-design`, `delivery-release-gate`, `bigdata-product-extension` when analytics pipelines are involved | Contract/delete phase before reconciliation. |
| Performance/reliability | Hot key, stampede, full scan, pool saturation, query p99, memory, retention, or cost risk. | Bound resource use and degradation before rollout. | Baseline, capacity/cost estimate, alert, backpressure or fallback. | `performance-budgeting`, `profiling`, `reliability-observability-gate` | Optimization without measured bottleneck. |

## Proactive Professional Triggers

- **Signal:** Redis/cache write has no TTL, invalidation, namespace owner, or tenant-safe key. **Hidden risk:** stale or cross-tenant state, memory growth, hot key. **Required professional action:** define key lifecycle and invalidation before merge. **Route to:** `cache-design`, `reliability-observability-gate`. **Evidence required:** key schema, TTL/invalidation path, memory/hit-rate metric, stale read test.
- **Signal:** SQL query changes without EXPLAIN/plan or realistic cardinality. **Hidden risk:** full scan, bad composite index, lock or pool saturation. **Required professional action:** validate plan and write overhead. **Route to:** `indexing-query-optimization`, `performance-budgeting`. **Evidence required:** EXPLAIN output, data volume, index rationale.
- **Signal:** data job, query, cache fill, replay, or export uses nested scans, full sort, load-all, or unbounded grouping. **Hidden risk:** wrong O(n squared) complexity, memory loss, stale hot-key assumptions, or runaway batch cost. **Required professional action:** require algorithm/data structure and streaming/chunking selection before implementation. **Route to:** `algorithm-data-structure-selection`, `language-performance-safety`. **Evidence required:** input size/distribution, complexity, memory budget, batch size, and benchmark/profile report.
- **Signal:** queue consumer commits offset/ACK before side effect is durable or idempotent. **Hidden risk:** lost work or duplicate side effects. **Required professional action:** redesign commit boundary and idempotency. **Route to:** `message-queue-design`, `idempotency-retry-design`. **Evidence required:** commit/ack point, duplicate-delivery test, replay plan.
- **Signal:** Kafka topic, consumer group, or partition key changes without ordering, DLQ, replay, retention, or idempotency semantics. **Hidden risk:** poison-message loops, out-of-order side effects, and unrecoverable replay gaps. **Required professional action:** define delivery contract before accepting the stream change. **Route to:** `message-queue-design`, `reliability-observability-gate`. **Evidence required:** partition key, ordering guarantee, DLQ/replay procedure, lag and poison-message test.
- **Signal:** search index mapping/reindex changes without dual index, alias cutover, or backfill progress. **Hidden risk:** missing/incorrect search results. **Required professional action:** plan reindex and consistency window. **Route to:** `search-analytics-design`, `delivery-release-gate`. **Evidence required:** index version, backfill/reconcile metrics, rollback alias.
- **Signal:** source-of-truth is unclear between DB/cache/search/warehouse/service. **Hidden risk:** permanent drift and conflicting writes. **Required professional action:** declare authoritative owner and derived-store refresh. **Route to:** `architecture-impact-reviewer`, `data-api-contract-changer`. **Evidence required:** owner, write path, reconciliation, consumer impact.
- **Signal:** backfill/replay job has no throttle, checkpoint, freshness SLA, or rollback. **Hidden risk:** production saturation, partial migration, unbounded cost. **Required professional action:** add checkpointed rollout and observability. **Route to:** `data-migration-design`, `reliability-observability-gate`. **Evidence required:** batch size, checkpoint, progress/lag metric, rollback procedure.
- **Signal:** write path updates database, cache, search, or queue state in separate steps without transaction, outbox, or reconciliation. **Hidden risk:** durable data and derived stores diverge after partial success. **Required professional action:** choose a consistency boundary and recovery path before implementation. **Route to:** `transaction-consistency`, `backend-change-builder`. **Evidence required:** transaction/outbox decision, reconciliation job, partial-failure test.
- **Signal:** repository/cache/queue/search errors are swallowed, generalized, or leaked as raw driver/SDK/database internals. **Hidden risk:** retryability and terminal failure are unclear, and diagnostics may leak internals. **Required professional action:** define data-layer failure contract. **Route to:** `failure-contract-design`, `logging-error-handling`. **Evidence required:** boundary translation map, retry/DLQ behavior, safe message, and negative tests.
- **Signal:** cache/event/search/index mutation is hidden in mapper, getter, policy, or model conversion. **Hidden risk:** side-effect ordering and source-of-truth drift. **Required professional action:** trace data and side-effect flow. **Route to:** `data-side-effect-flow-tracing`, `cache-design`. **Evidence required:** flow map, source of truth, transaction/outbox ordering, and idempotency/compensation.
- **Signal:** DB/cache/queue/search tests need private repository helpers, live infrastructure, wall-clock timing, random IDs, or broad shared fixtures to pass. **Hidden risk:** middleware tests become flaky or implementation-coupled while real boundary behavior remains unproven. **Required professional action:** design explicit test seams and contract/integration proof. **Route to:** `testability-seam-design`, `quality-test-gate`. **Evidence required:** public repository/queue/cache boundary, fake/stub/contract decision, deterministic controls, fixture owner, and validation output.

### Decision Tree: Index Design Required?

```
Is a new query being added or an existing query being modified?
├── Yes → Run EXPLAIN ANALYZE against realistic data volume
│   ├── Sequential scan on high-traffic table? → New index required
│   └── Existing index used inefficiently? → Composite index or covering index
Is an existing index being dropped?
├── Yes → Confirm no active query plan uses it (pg_stat_user_indexes)
Is a new column being added to an indexed table?
├── Yes → Assess if composite index needs updating
No query change → No index change required
```

## Risk Escalation Rules
- Escalate when an `ALTER TABLE` will lock a table with > 100k rows — requires online migration planning (pt-online-schema-change, pg_repack, or copy-and-swap).
- Escalate when a cache stampede risk exists: many concurrent requests for the same cold cache key with expensive database queries behind it.
- Escalate when at-least-once queue semantics are used for operations with financial, authorization, or data-corruption side effects — idempotency design is required.
- Escalate when a search re-index is required that will produce a gap in search availability during the migration.
- Escalate when replication lag affects a decision that cannot tolerate stale data (duplicate check, balance validation, authorization).
- Escalate when cross-region data replication consistency is involved — the consistency model and partition tolerance behavior must be documented and approved.
- Escalate when data retention policy changes affect legal hold, compliance, or audit obligations.
- Escalate when stream processing topology changes affect downstream consumers that have not been notified.

## Critical Details
- **N+1 query elimination**: Application code that calls a database once per result item is an N+1 query. Fix with eager loading (`JOIN`), batch fetch (`WHERE id IN (...)`), or a dedicated aggregate query. N+1 queries are invisible in development and catastrophic at production load.
- **Optimistic locking pattern**: Use a `version` column incremented on every update — `UPDATE ... WHERE id = :id AND version = :expected_version` returns 0 rows when a concurrent update wins; the application retries or returns a conflict error.
- **TTL granularity**: Redis TTL is per-key; expiry of a parent key does not expire related child keys — model key namespaces carefully to avoid orphaned cache entries.
- **Kafka partition key design**: Messages with the same partition key are delivered in order within a partition. Choosing `user_id` as partition key provides per-user ordering but creates hot partitions for high-activity users. Use a `tenant_id + entity_id` composite for balanced distribution.
- **PostgreSQL partial indexes**: `CREATE INDEX ... WHERE deleted_at IS NULL` indexes only active rows — dramatically reduces index size and write cost for soft-delete patterns.
- **DynamoDB access pattern discipline**: Every table must be designed for its access patterns before creation — adding a new access pattern later may require a new Global Secondary Index (GSI) with backfill cost or a table redesign.
- **Elasticsearch analyzer selection**: The `standard` analyzer lowercases and tokenizes; `keyword` preserves exact values for sorting and filtering; `english` stems words for full-text relevance. Choose per field based on query type, not as a default.

### Anti-Examples

| Data Layer Pattern | Problem | Corrected Approach |
|---|---|---|
| `SELECT * FROM users WHERE email = 'x'` with no index on `email` | Full table scan at scale | `CREATE INDEX CONCURRENTLY idx_users_email ON users (email)` |
| Cache TTL = 1 hour for payment status | Stale status misleads users | Explicit invalidation on payment state change + short TTL (60 s) fallback |
| Queue consumer: `try { process() } catch { skip }` | Poison messages silently disappear | Route failed messages to DLQ with message metadata; alert on DLQ depth |
| Read balance from replica before debit | Replication lag allows overdraft | Read balance from primary for all financial operations |
| Elasticsearch re-index in-place during traffic | Mapping conflict breaks documents | Create new index, populate in background, alias cutover when ready |

## Failure Modes
- **Wrong source of truth creates permanent drift**: Two services write to different stores for the same entity — periodic reconciliation never fully closes the gap.
- **Missing indexes degrade production under load**: A query that takes 5 ms with an index takes 8,000 ms with a sequential scan on a table that grew from 10k to 10M rows.
- **Stale cache serves incorrect state**: A subscription is cancelled but the cache still shows active — the user performs actions they are no longer entitled to.
- **Queue retries duplicate side effects**: A payment event is processed twice because the consumer crashes after committing the side effect but before committing the offset.
- **Search re-indexing loses documents**: A mapping change during peak traffic causes Elasticsearch to reject documents that don't match the new mapping — they are dropped silently.
- **Cache stampede**: 500 concurrent requests hit an expired popular cache key simultaneously — all 500 go to the database, which times out, causing a cascading failure.
- **Replication lag causes double-spend**: A balance check reads a replica showing $100 available; a concurrent debit already ran on the primary reducing it to $0; the second debit succeeds because the replica had stale data.
- **Large migration locks table**: An `ALTER TABLE ADD COLUMN NOT NULL DEFAULT ...` on a 200M row table takes an exclusive lock for 45 minutes — all writes block, API times out, P1 incident.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a data and middleware change plan with:
- **Mode selected**: new store/access path, modify existing, bug fix, queue/stream reliability, migration/backfill, or performance/reliability, with trigger signal.
- **Boundaries inspected**: schemas, queries, indexes, cache keys, invalidation paths, queue topics/consumer groups, search indexes, object storage paths, migrations, backfills, and downstream consumers inspected or skipped with reason.
- **Professional judgment**: source-of-truth, consistency, delivery, freshness, capacity, or recovery decision made, and data risks ruled out or retained.
- **Source-of-truth declaration**: Authoritative store for each entity and derived store relationships.
- **Consistency model**: Strong/eventual/causal per operation, with replication lag tolerance analysis.
- **Access pattern inventory**: Queries driving the design, with frequency and cardinality estimates.
- **Index strategy**: New indexes with justifying queries; dropped indexes with query plan evidence.
- **Cache design**: Key structure, TTL, invalidation strategy, stampede mitigation.
- **Queue design**: Delivery semantics, DLQ routing, poison message handling, retry policy.
- **Algorithm/data-structure decision**: input scale, complexity, memory budget, streaming/chunking/batch size, hot-key/skew handling, and rejected load-all or nested-scan alternatives.
- **Failure contract**: driver/repository/cache/queue/search error translation, retryable versus terminal states, DLQ behavior, and safe diagnostics.
- **Data and side-effect flow**: transaction/outbox ordering, cache/search/event mutation visibility, source of truth, idempotency, and compensation.
- **Dependency lifecycle**: reusable client/pool ownership, connection lifecycle, shutdown cleanup, and config binding when middleware clients or pools change.
- **Migration plan**: Forward migration steps; rollback migration; online vs. offline strategy; execution window.
- **Failure mode analysis**: Named failure scenarios with prevention or recovery strategy.
- **Reuse and placement rationale**: why each index, cache key, queue topic, migration, backfill, or derived-store update belongs at this storage/middleware boundary.
- **Behavior preservation**: read/write semantics, freshness, ordering, rollback, and old application compatibility preserved or intentionally changed.
- **Test obligations**: Query plan tests, cache invalidation tests, DLQ tests, migration tests.
- **Observability**: Metrics (query latency, cache hit rate, queue depth, DLQ depth) and alert thresholds.
- **Validation evidence**: EXPLAIN/plan, cache, queue, migration/backfill, replay, and observability checks run, with residual risk and next gate.
- **Evidence limits**: what each plan/test/metric proves and what it does not prove about production cardinality, replay scale, tenant isolation, stale reads, or downstream consumers.

## Evidence Contract
Close a data or middleware change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, source-of-truth declaration, consistency model, delivery semantic, freshness target, or access pattern the change rests on.
- **Files and boundaries inspected**: schemas, queries, indexes, cache keys, invalidation paths, queue topics/consumer groups, search indexes, migrations/backfills, and downstream consumers read, and the invalidation or offset-commit boundary confirmed.
- **Placement rationale**: why each index, cache key, queue, or migration step is shaped as it is, with the rejected alternative and its query-plan or throughput evidence.
- **Validation commands**: the query-plan, cache-invalidation, DLQ/replay, TTL, migration-rollback, backfill, and freshness checks run, each with its outcome and what it proves/does not prove.
- **What evidence proves / what it does not prove**: map every EXPLAIN plan, cache test, replay test, migration test, metric, or reconciliation report to the exact data correctness claim it proves and the scale, tenant, ordering, lag, or rollback claim it does not prove.
- **Data judgment and handoff**: mode selected, source-of-truth/consistency judgment, behavior preservation, evidence limits, and next gate.
- **Residual risk**: the stampede, hot-key, lag, ordering, stale read, data drift, cost, or partial-migration path that remains untested or assumed, and the named owner of the follow-up.

## Quality Gate
1. Source of truth is declared for every entity affected by the change.
2. Consistency model is explicit for every read/write path — no implicit assumptions about replication lag.
3. Every new or modified query has been validated with `EXPLAIN ANALYZE` against realistic data volume.
4. Every new index has a named query it serves; no speculative indexes.
5. Cache invalidation strategy is explicit — no implicit TTL-only invalidation for mutable state.
6. Queue delivery semantics are declared and consumers handle declared semantics correctly (idempotency for at-least-once).
7. DLQ routing and alerting exist for all queue consumers.
8. Every migration has a tested rollback migration.
9. Large table migrations use online migration strategies — no exclusive locks on high-traffic tables.
10. Failure mode analysis covers: stale cache, queue duplicate, replication lag, and migration rollback failure.

## Handoff
- **data-api-contract-changer** — when schema changes affect API contract compatibility or consumer migration.
- **backend-change-builder** — for application-layer implementation of cache invalidation, queue consumers, or query logic.
- **reliability-observability-gate** — when cache, queue, or database changes affect SLO paths or require new alert coverage.
- **quality-test-gate** — for migration test design, cache invalidation tests, and DLQ routing tests.
- **delivery-release-gate** — for migration execution windows, online migration tooling, and rollback verification.
- **architecture-impact-reviewer** — when the data layer change introduces a new consistency boundary, replication topology, or cross-service data ownership.
- **algorithm-data-structure-selection** — when data processing shape, batch size, grouping, sorting, top-K, or memory budget is unclear.
- **failure-contract-design** — when repository, driver, cache, queue, or search failure semantics are unclear.
- **data-side-effect-flow-tracing** — when cache/event/search/persistence side effects may be hidden or misordered.
- **dependency-wiring-lifecycle** — when client, pool, subscription, stream, or shutdown ownership changes.
- **testability-seam-design** — when middleware tests need deterministic DB/cache/queue/search seams or risk private-helper coupling.

## Completion Criteria
Data and middleware changes are ready when source of truth is declared, consistency model is explicit, indexes are justified by access patterns with EXPLAIN evidence, cache invalidation is deterministic, queue semantics and DLQ routing are defined, every migration has a tested rollback, large table changes use online strategies, and failure modes for stale cache, queue duplication, replication lag, and migration rollback are explicitly analyzed.
