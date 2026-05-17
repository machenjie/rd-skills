---
name: nosql-database
description: Selects NoSQL storage only when access patterns, schema flexibility, scale model, and consistency boundaries justify it.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "46"
changeforge_version: 0.1.0
---

# Mission

**Decide and design NoSQL database changes only when the access patterns, data shape, scale model, and consistency boundaries make non-relational storage the safer production choice** — ensuring that partition key design, consistency guarantees, denormalization ownership, schema versioning, and operational limits are explicit before any non-relational store enters production.

# When To Use

Use this capability when a change: proposes document, key-value, wide-column, graph, time-series, or other non-relational storage; adds indexes, collections, partitions, or item schemas to an existing NoSQL store; changes the partition/sort key design, consistency level, or TTL on existing data; introduces denormalization that duplicates data across multiple items or collections; or is flagged in review for "hot partition", "unbounded document growth", "missing schema validation", or "cross-partition transaction."

# Do Not Use When

Do not use this capability to avoid relational modeling, constraints, referential integrity, or JOIN-based queries when the product invariants require them. Do not use it to justify choosing NoSQL because "it's more modern" or "it scales better" without concrete access pattern evidence. Do not use it as a substitute for `relational-database` when the data is inherently relational and multi-entity transactional consistency is required.

# Non-Negotiable Rules

- **Define access patterns before choosing keys.** NoSQL key design is irreversible in most stores (DynamoDB table key cannot be changed; Cassandra partition key requires new table). Access patterns drive key design: partition key = what you filter on; sort key = what you range-scan on; secondary index = additional access path at cost. Designing keys before access patterns guarantees incorrect design.
- **State the consistency model and which invariants are eventually consistent.** DynamoDB default reads are eventually consistent. Cassandra `QUORUM` vs `ONE`. MongoDB read preference `primaryPreferred` vs `primary`. Eventually consistent reads can return stale data. Every invariant that must be correct (balance, inventory count, lock state, permission) must identify whether it is eventually consistent or strongly consistent — and if eventually consistent, what happens when a client reads stale data.
- **Avoid cross-item / cross-partition transactions unless explicitly supported.** DynamoDB TransactWrite supports up to 100 items in a single transaction. MongoDB supports multi-document ACID within a replica set. Cassandra: no cross-partition transactions. If the business invariant requires atomically updating two items in different partitions, and the database does not support it, the design must use a compensating transaction, saga, or outbox pattern — not just assume atomicity.
- **Partition keys must be high-cardinality to avoid hot partitions.** A partition key with low cardinality (e.g., `status = 'pending'`) routes all writes to one shard or partition. In DynamoDB: throughput is partitioned; a hot partition exhausts its capacity and causes throttling. In Cassandra: a large partition causes compaction and GC pressure. Rule: use entity ID (`userId`, `orderId`) as partition key; use status-based access via Global Secondary Index (GSI).
- **Denormalized data requires explicit ownership and update propagation.** NoSQL denormalization (duplicating `userName` in `Order` documents to avoid a join) trades consistency for read performance. The trade-off is only acceptable if: (a) the source of truth is identified (User owns `userName`); (b) the propagation mechanism is defined (on User update, fan-out to all Order documents — or accept eventual staleness within TTL); (c) drift detection exists (periodic reconciliation job or consistency check).
- **Schema versioning is mandatory for document stores.** JSON documents in MongoDB, DynamoDB, or Firestore have no enforced schema. Without versioning, a code change that adds a required field breaks all readers of documents written before the migration. Every document type must carry a `schemaVersion` field (or equivalent). Readers must handle old schema versions gracefully.
- **Define document size, partition size, and index limits before production.** DynamoDB: 400KB item size limit; 10GB per partition before split; 25 GSIs per table; 40KB max GSI item size. MongoDB: 16MB BSON document limit; unbounded collection growth requires TTL indexes or archival. Cassandra: 100MB partition size practical limit (larger causes compaction issues). These limits must be validated against projected data volume before deploying to production.

# Industry Benchmarks

Anchor against: **Alex DeBrie "The DynamoDB Book"** — single-table design; access-pattern-first modeling; GSI overloading; adjacency list pattern; composite sort key pattern. **AWS DynamoDB Best Practices** (docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html) — partition key design, GSI design, item collections, DynamoDB Streams + Lambda for fan-out. **MongoDB Schema Design Anti-Patterns** (mongodb.com/developer/products/mongodb/schema-anti-patterns) — massive arrays, bloated documents, unnecessary indexes, separating data that is accessed together. **Martin Fowler "NoSQL Distilled"** (2012, with Pramod Sadalage) — aggregate-oriented databases; key-value, document, column-family, graph; consistency model taxonomy. **CAP theorem (Brewer)** — Consistency, Availability, Partition Tolerance; any distributed system can guarantee only 2 of 3. **PACELC model (Daniel Abadi)** — extends CAP: during Partition: C vs A; Else (no partition): Latency vs Consistency. **Apache Cassandra Data Modeling** — partition key design; clustering columns; Cassandra Anti-Patterns (secondary indexes on high-cardinality columns, allow filtering, UDTs in partition key). **Google Firestore / Bigtable** — hierarchical document model; composite indexes; query limitations (no inequality on two different fields). **Redis data structure design** — key naming conventions; TTL discipline; memory eviction policies; persistence (AOF vs RDB). **Time-series: InfluxDB / TimescaleDB** — measurement + tag design; retention policies; downsampling; cardinality limits on tags.

### NoSQL Store Selection Matrix

| Use Case | Recommended Store | Avoid | Key Design Pattern |
| --- | --- | --- | --- |
| Flexible documents, complex queries | MongoDB | DynamoDB for ad-hoc queries | Entity ID as primary key; compound indexes |
| High-scale key-value with predictable access | DynamoDB | MongoDB for unpredictable query patterns | Partition key = entity type#id, sort key = SK#value |
| Graph traversal (social, recommendation) | Neo4j / Amazon Neptune | Document store | Node + Relationship model |
| Time-series (metrics, IoT, logs) | InfluxDB / TimescaleDB | DynamoDB (wrong model) | Measurement + tags + timestamp |
| Session, cache, ephemeral state | Redis | MongoDB (overkill) | Key = session:{userId}; TTL mandatory |
| Wide-column, write-heavy, time-partitioned | Cassandra / HBase | DynamoDB (cost at scale) | Partition by entity; cluster by time |
| Search / full-text | Elasticsearch / OpenSearch | Any of the above | Inverted index; mapping types |

### DynamoDB Access Pattern Design Template

```
Table design starts with access patterns, NOT with entity structure.

Step 1: List ALL access patterns:
  AP1: Get user by userId              → PK: USER#<userId>     SK: PROFILE
  AP2: Get orders for user             → PK: USER#<userId>     SK: ORDER#<orderId>
  AP3: Get order by orderId            → GSI1-PK: ORDER#<orderId>
  AP4: Get orders by status (admin)    → GSI2-PK: STATUS#<status>  (low cardinality → accept hot partition for admin-only read)

Step 2: Define key schema from access patterns:
  PK: USER#<userId>  /  SK: ORDER#<orderId>
  GSI1: ORDER#<orderId>  (overloaded index for direct order lookup)

Step 3: Define item shape:
  {
    "PK": "USER#u123",
    "SK": "ORDER#o456",
    "schemaVersion": 2,
    "orderId": "o456",
    "userId": "u123",
    "status": "confirmed",
    "totalCents": 4999,
    "createdAt": "2026-01-15T14:00:00Z",
    "GSI1PK": "ORDER#o456"
  }

Anti-patterns:
  ❌ PK = userId (string only) — cannot distinguish User items from Order items in single-table design
  ❌ SK = timestamp alone — cannot retrieve specific entity without scan
  ❌ GSI on status with low cardinality — hot partition; use for read-heavy admin queries only with careful capacity
  ❌ Storing large JSON blobs (>100KB) as attribute — nearing 400KB limit; causes expensive reads
```

### Consistency Level Decision Matrix

| Invariant | Consistency Required | DynamoDB | MongoDB | Cassandra |
| --- | --- | --- | --- | --- |
| Financial balance / ledger | Strong | `ConsistentRead=true` | `primary` read preference | `QUORUM` or `ALL` |
| Inventory count (purchase gate) | Strong | `ConsistentRead=true` + optimistic lock | `findOneAndUpdate` with version | `QUORUM` |
| User profile display | Eventual OK | Default (eventually consistent) | `primaryPreferred` | `ONE` |
| Session / presence | Eventual + TTL | Default + TTL attribute | — | `ONE` + TTL |
| Audit / append-only log | Strong write, eventual read | `TransactWrite` + `ConsistentRead` | `writeConcern: majority` | `QUORUM` write |

# Selection Rules

Select this capability when: a non-relational store is being proposed or needs its schema, key design, or index structure changed. Route elsewhere when: **relational-database** is primary (strong referential integrity, complex joins, multi-table ACID transactions are required); **cache-design** is primary (the store is purely an acceleration layer, not the system of record); **search-analytics-design** is primary (full-text search, relevance ranking, faceting, or OLAP queries); **data-model-design** is primary (domain entity modeling independent of persistence technology).

# Risk Escalation Rules

Escalate when: NoSQL is proposed for financial records, ledger data, or any invariant that requires atomic multi-entity updates; the partition key has low cardinality (< 10 distinct values under production load); the data volume will exceed DynamoDB 400KB item limit or Cassandra 100MB partition limit within 12 months; cross-partition transactions are assumed without confirming database support; the store is proposed for regulated data (PII, PAN, PHI) without defining encryption at rest, access logging, and data retention policy; or denormalized data has no defined authoritative writer and no drift detection mechanism.

# Critical Details

- **Single-table design (DynamoDB) is powerful but requires upfront access pattern completeness.** A single DynamoDB table with overloaded keys (`PK`, `SK`) can serve multiple entity types and access patterns with one table, avoiding JOIN operations and reducing costs. But every access pattern must be identified upfront — adding a new access pattern later may require backfilling all existing items to add a new GSI attribute, which is expensive on large tables.
- **MongoDB schema validation should be enforced in production.** Although MongoDB is "schemaless," MongoDB 3.6+ supports JSON Schema validation via `$jsonSchema` validator on collections. This should be enforced in production to prevent invalid documents. Without it, code changes that add required fields silently break on old documents at read time.
- **TTL (Time-To-Live) is a cost and safety control, not just a convenience.** In DynamoDB, items without TTL persist indefinitely and accumulate cost. In Redis, keys without TTL never expire and consume memory until eviction. Every ephemeral item (sessions, rate limit counters, OTP codes, job locks) must have a TTL. Define TTL at schema design time — retrofitting TTL on millions of items is expensive.
- **Global Secondary Indexes (GSI) in DynamoDB are asynchronously replicated.** A GSI is eventually consistent with the base table by default. If you write an item and immediately query the GSI, the item may not appear. For read-after-write correctness, use `ConsistentRead=true` on the base table; for GSI reads, design the flow to tolerate eventual consistency or use a different access pattern.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| DynamoDB PK = `status` (low cardinality) | All `pending` orders route to one partition shard; throughput throttled | PK = `ORDER#<orderId>`; use GSI for status-based admin queries |
| MongoDB document with no `schemaVersion` field | Code change adds required field; old documents fail at read time | Add `schemaVersion: 1` to all documents; readers handle old versions gracefully |
| Cassandra `ALLOW FILTERING` query in production | Full cluster scan; latency grows with data volume | Redesign partition key to support query; or add materialized view |
| DynamoDB item stores 500KB JSON blob per user | Exceeds 400KB limit; write fails | Split into multiple items with SK segmentation or store blob in S3; store S3 key in DynamoDB |
| No TTL on Redis session keys | Memory fills at rate of user signups; Redis OOM eviction; session corruption | Set `EX` (seconds) on all session writes; document TTL in schema |
| Denormalized `userName` in 10M Order documents, no update propagation | User changes name; Orders show stale name indefinitely | Define propagation: publish `UserNameChanged` event; update Orders asynchronously OR accept staleness with business sign-off |

# Failure Modes

- DynamoDB partition key set to `tenantId` for a multi-tenant SaaS — one large tenant generates 80% of writes; hot partition; capacity exhausted for other tenants; DynamoDB throttles entire table.
- MongoDB collection has no schema validation — after 18 months of incremental development, 8 different document shapes exist; code branches on shape detected at runtime; impossible to reason about invariants.
- DynamoDB item size grows unboundedly (list attribute appended on every event) — after 3 weeks in production, item exceeds 400KB; writes fail with `ValidationException: Item size has exceeded the maximum allowed size`; data loss.
- Cross-partition transaction assumed in Cassandra — payment deduction and inventory reservation written in separate partition key batches; failure after first write leaves account debited but inventory not reserved.
- No TTL on DynamoDB rate-limit counter — rate limits never reset; legitimate users permanently blocked after single burst.
- MongoDB query uses `$regex` without index — full collection scan; latency grows linearly with collection size; 50ms at 1M documents becomes 5 seconds at 100M documents.

# Output Contract

Return a NoSQL design with:

- `store_selection` (store type, version; justification against alternatives; specific access pattern evidence)
- `access_patterns` (complete list: AP1..N; for each: query type, filter fields, sort fields, result shape, expected volume)
- `key_schema` (partition key, sort key, justification for each; GSI definitions with PK/SK/projected attributes)
- `item_schema` (field names, types, `schemaVersion`, TTL attribute if applicable; max projected item size)
- `consistency_model` (per-invariant: strongly consistent vs eventually consistent; which operations use `ConsistentRead=true` or `QUORUM`)
- `denormalization_rules` (which fields are duplicated; authoritative source; propagation mechanism; drift detection)
- `schema_versioning` (version field name; how readers handle old versions; migration plan)
- `capacity_limits` (projected item count, item size, partition size, GSI count; validated against store limits)
- `operational_limits` (DynamoDB: WCU/RCU baseline; Cassandra: compaction strategy; MongoDB: index count)
- `failure_modes` (hot partition, item size overflow, stale read, cross-partition transaction failure — mitigation for each)
- `migration_plan` (backfill strategy; dual-write period; cutover; rollback)
- `observability` (read/write latency, throttling/exception rate, partition heat, document size percentiles)
- `test_strategy` (assert: large item rejected; stale read handled; hot partition simulation; TTL expiration)

# Quality Gate

The design is complete only when:

1. Every access pattern is listed and each one maps to a key or index design.
2. Partition key has sufficient cardinality (no low-cardinality values at the top level of writes).
3. Consistency model is explicit for every invariant that must be correct.
4. Cross-partition/cross-item transactions either use supported database feature or have a Saga/Outbox alternative.
5. Every document type carries a `schemaVersion` (or equivalent) with a reader backward-compatibility policy.
6. TTL defined for all ephemeral data (sessions, counters, locks, OTP).
7. Projected item/document size validated against store limits (DynamoDB: < 400KB; Cassandra: < 100MB partition).
8. Denormalization ownership and propagation mechanism are explicit.
9. Capacity limits validated against projected production data volume.
10. NoSQL choice justified with access pattern evidence (not merely convenience or trend).

# Used By

- data-middleware-change-builder

# Handoff

Hand off to `data-model-design` for domain entity structure independent of persistence technology; `relational-database` when constraints, joins, or ACID multi-table transactions are required; `transaction-consistency` for Saga or Outbox patterns when cross-item atomicity is needed; `cache-design` for acceleration layers on top of the NoSQL store; `data-migration-design` for backfill and schema migration planning.

# Completion Criteria

The capability is complete when **NoSQL use is justified by concrete access patterns, partition key design supports all required queries without hot partition risk, consistency model is explicit per invariant, schema versioning prevents backward-incompatibility failures, all data size and operational limits are validated, and denormalization has a defined authoritative writer and propagation strategy**.

# Completion Criteria

The capability is complete when the NoSQL design can satisfy named access patterns without hidden consistency, partition, schema, or repair risks.
