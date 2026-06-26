# NoSQL Database Benchmarks And Patterns

Use this reference when NoSQL database output needs detailed store-selection, access-pattern, consistency, or operational-limit examples that would make the main `SKILL.md` too large. Keep the main body focused on routing, ownership, evidence, output contract, and quality gates.

## Benchmark Anchors

- DynamoDB access-pattern-first modeling, single-table design, composite sort keys, GSI overloading, item collections, and Streams-based fan-out.
- MongoDB document design anti-patterns, JSON Schema validation, index discipline, document size limits, and embedding vs reference rules.
- Cassandra and HBase wide-column modeling with partition key, clustering columns, compaction strategy, and no cross-partition transaction assumption.
- Firestore and Bigtable query constraints, composite indexes, hierarchical documents, and hotspot avoidance.
- Redis key/value design for ephemeral state, TTL discipline, memory policy, and durability limitations.
- Graph database modeling for node/relationship traversal workloads where edges are first-class data.
- Time-series stores for tag cardinality, retention, downsampling, and write-heavy time-partitioned workloads.
- CAP and PACELC models for consistency/availability/latency tradeoffs in distributed data stores.
- Kleppmann, Fowler, and Sadalage aggregate-oriented data modeling for choosing document/key-value/column-family storage by access pattern and consistency boundary.

## Store Selection Matrix

| Workload | Candidate store | Avoid when | Required proof |
| --- | --- | --- | --- |
| Flexible documents read together | MongoDB / Firestore | Multi-entity ACID, arbitrary joins, strict relational constraints. | Document shape, validator, query/index map, schemaVersion policy. |
| High-scale key lookup with predictable patterns | DynamoDB / key-value | Unknown ad-hoc query patterns, low-cardinality access, cross-item invariants. | AP list, PK/SK/GSI map, item size, capacity and cost estimate. |
| Wide-column write-heavy time/range access | Cassandra / HBase / Bigtable | Need cross-partition transactions or ad-hoc filtering. | Partition/clustering key, partition size, compaction, query table per access pattern. |
| Graph traversal | Neo4j / Neptune | Simple lookup or tabular reporting is enough. | Node/edge model, traversal depth, relationship cardinality, permission model. |
| Time-series metrics/events | InfluxDB / TimescaleDB / Cassandra | Need mutable business records or relational joins. | Measurement/tags, tag cardinality, retention, downsampling, late data behavior. |
| Ephemeral session/cache state | Redis / Memcached | Durable source-of-truth records are required. | TTL, eviction policy, cache-loss behavior, persistence decision. |
| Full-text or analytics | OpenSearch / ClickHouse / BigQuery | Source DB or NoSQL key lookup serves the need. | Relevance/OLAP requirement, ingestion freshness, reindex/drift plan. |

## DynamoDB Access Pattern Template

```text
Design order:
1. List access patterns before table keys.
2. Classify consistency and volume per access pattern.
3. Map each pattern to PK/SK or GSI.
4. Check hot partition, item collection size, item size, and write amplification.

AP1: Get user profile by userId
  Query: PK = USER#<userId>, SK = PROFILE
  Consistency: strong if profile controls permission/eligibility; eventual for display-only.

AP2: List orders for user by createdAt
  Query: PK = USER#<userId>, SK begins_with ORDER# sorted by createdAt
  Volume: expected max orders per user; item collection growth checked.

AP3: Get order by orderId
  Query: GSI1PK = ORDER#<orderId>
  Note: GSI eventual consistency accepted only if caller can tolerate read lag.

AP4: Admin list by status
  Query: GSI2PK = STATUS#<status>#BUCKET#<bucket>
  Note: status alone is low cardinality; bucket or alternate projection required for write-heavy path.
```

## Consistency Decision Matrix

| Invariant or read | Strong consistency required? | Accept eventual consistency only when | Evidence |
| --- | --- | --- | --- |
| Financial balance or ledger | Yes | Never for authoritative decision. | Strong read/write, single invariant owner, reconciliation. |
| Inventory purchase gate | Yes | Search/listing may be eventual if checkout revalidates source of truth. | Source verification before commit, stale UI behavior. |
| Permission or entitlement | Usually yes | Cached or projected view has short TTL plus invalidation and denial-safe fallback. | Revocation path, stale-read consequence, audit. |
| User profile display | No | Staleness is cosmetic and bounded. | Lag budget and refresh behavior. |
| Audit append log | Strong write, eventual read may be acceptable | Readers tolerate lag and cannot mutate audit state. | Write durability, retention, query lag. |
| Derived catalog/search card | No, if source revalidated for critical actions | Product accepts freshness SLO. | Projection lag metric, drift repair, fallback. |

## Operational Limit Checklist

- Item/document size: projected p50/p95/p99 plus hard maximum.
- Partition/item-collection size: max rows/documents per partition key, top-tenant/time-bucket skew, and split strategy.
- Index count and projection size: every secondary index has a beneficiary access pattern and write-cost estimate.
- Throughput and cost: expected RCU/WCU, read/write rate, burst behavior, autoscaling or provisioned capacity, and budget ceiling.
- TTL/retention: what expires, what must never expire, and how erasure/archive requirements interact with TTL.
- Backup and restore: point-in-time recovery, snapshot scope, restore test, and rebuild path for derived projections.
- Observability: throttle rate, consumed capacity, hot key/partition, item size, index lag, replication lag, drift, and cost alarms.

## Validation Patterns

| Risk | Validation evidence |
| --- | --- |
| Hot partition | Synthetic or analytical key-distribution check using expected tenant/status/time skew. |
| Unsupported query | Access-pattern map proves every query has key/index support; no scan fallback. |
| Old document breakage | Reader compatibility test for old and new `schemaVersion`; migration/backfill validation query. |
| Stale GSI read | Test or design proof that caller tolerates lag or revalidates against base/source. |
| Denormalization drift | Reconciliation query/job and replay/repair procedure. |
| TTL behavior | Expiration test or store-level TTL configuration review plus "must not expire" list. |
| Item overflow | Size estimate with representative max document/item; split or blob-reference plan. |
| Cross-partition atomicity | Supported transaction proof or Saga/Outbox/compensation design. |

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Choosing NoSQL before listing queries. | Key/index design cannot be validated and later access patterns require backfill. | Build AP1..N and map each to key/index or rejected alternative. |
| Partition key is `status` or `date`. | Low-cardinality or bursty key creates hot partitions. | Add high-cardinality component, bucket, or query-specific projection. |
| Document shape has no version. | Old data breaks when readers expect new required fields. | Add schemaVersion and backward-compatible reader/upcaster. |
| Denormalized copy has no owner. | Data drifts indefinitely after source updates. | Name writer authority, event propagation, lag budget, reconciliation. |
| GSI read used for immediate correctness. | GSI may lag after write. | Use strong base-table read or source-of-truth revalidation. |
| Redis used as durable database by default. | Eviction, restart, or failover can lose authoritative data. | Use Redis as cache/ephemeral state or design durability/recovery explicitly. |
| Cassandra `ALLOW FILTERING` in production. | Cluster scan grows with data and bypasses modeling discipline. | Build query-specific table keyed for that access pattern. |
