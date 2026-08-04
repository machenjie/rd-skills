# NoSQL Database Benchmarks And Patterns

Load this reference when a non-relational store, partition/key/document model, consistency boundary, denormalized projection, or operational limit is being selected or changed. Do not load it when the current relational/source store already satisfies the access and correctness contract.

## Workload And Store Fit

| Workload | Candidate family | Reject or escalate when | Required proof |
| --- | --- | --- | --- |
| Predictable key/range lookup | Key-value or wide-column. | Ad-hoc queries, low-cardinality hot keys, joins, or cross-partition invariants dominate. | Complete access-pattern map, key/index mapping, skew, capacity, and cost. |
| Aggregate-shaped documents | Document store. | Independent sub-entity updates, large/unbounded arrays, or cross-document invariants dominate. | Embed/reference rule, document maximums, schema/version, indexes, and update contention. |
| Relationship traversal | Graph store. | Bounded lookup/reporting is simpler in the current store. | Node/edge authority, depth/cycle/cardinality, permission, and traversal budget. |
| Time-series or high-write ranges | Time-series/wide-column store. | Mutable business records or cross-series consistency is required. | Tags/cardinality, partition/time bucket, retention, late data, downsampling, and repair. |
| Ephemeral state | Cache/key-value store. | Loss or eviction would destroy authoritative state. | TTL/eviction, persistence choice, source rebuild, and failure behavior. |
| Search/analytics projection | Search or columnar derived store. | It is being used as authority without explicit ownership. | Source, ingestion/deletion, freshness, drift/reindex, and fallback. |

Before designing keys, inventory current in-scope read, write, update, delete, and scan patterns found through code, telemetry, or owner evidence. For each discovered pattern, record actor or tenant scope, consistency need, expected and worst-case volume, ordering or range, and latency. Also record its index or key path and rejected scan or secondary-store alternative. Record unknown consumers as proof limits.

## Easy-To-Miss Boundaries

- Partition keys need distribution evidence for top tenant/status/time bursts, not average cardinality. Bound partition/item-collection/document size and define split/bucket/overflow behavior.
- Strong versus eventual reads are chosen per invariant consequence. A stale projection may serve browsing when critical actions revalidate the source and the UI or consumer handles bounded lag safely.
- Denormalized copies name writer authority, propagation order, lag budget, delete/visibility propagation, reconciliation, and replay. “Eventually consistent” is incomplete without repair ownership.
- Classify each invariant as single-item or document, single-partition, or cross-partition. The evidence proves the selected store transaction or conditional-write boundary and covers cross-boundary recovery, idempotency, reconciliation, and partial effects.
- Old documents/items remain readable through a schema/version/default/upcast strategy; required fields, type changes, index creation, backfill, mixed versions, and rollback need current evidence.
- Secondary indexes have a beneficiary access pattern plus write amplification, storage, lag, and cost evidence. No unsupported query silently falls back to a full scan/filter.
- Define throughput/burst ceilings, retry/throttle behavior, backup/restore or rebuild, TTL/retention, hot-key/lag/drift/item-size signals, and provider limits from current documentation/configuration rather than remembered constants.

## Evidence And Proof Limits

Use representative maximum-size items and skewed key distributions, old/new schema fixtures, stale-index cases, duplicate/reordered propagation, and cross-partition failure cases where applicable. Local emulators and synthetic loads do not prove provider limits, production distribution, live cost, global consistency, or restore behavior.

Reject store-first design, low-cardinality hot keys, unversioned documents, and secondary-index or projection reads used for immediate correctness without revalidation. Also reject authoritative data in an eviction-prone cache by default, unowned denormalization, and scans hidden behind convenient APIs.

Route source modeling to `data-model-design`, migration to `data-migration-design`, cross-boundary consistency to `transaction-consistency`, search/OLAP to `search-analytics-design`, cache-only needs to `cache-design`, capacity to `performance-budgeting`, and recovery/operations to `backup-recovery` or `reliability-observability-gate`.
