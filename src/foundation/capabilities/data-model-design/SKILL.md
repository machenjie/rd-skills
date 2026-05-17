---
name: data-model-design
description: Designs data models from invariants, query patterns, ownership, lifecycle, migration risk, concurrency behavior, regulatory requirements, and separation between persistence internals and external contracts.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "25"
changeforge_version: 0.1.0
---

# Mission

Design data models that **encode domain invariants as close to the source of truth as possible, support required query and write patterns without future emergency rewrites, enforce ownership and lifecycle boundaries, minimize migration risk through deliberate evolution planning, and cleanly separate persistence internals from API contracts** — so that the system remains correct under concurrent writes, query demands, team autonomy, and regulatory requirements.

# When To Use

Use this capability when a change: introduces a new entity, aggregate, or document; adds, removes, or renames attributes or columns; changes relationships or cardinality (1:1, 1:N, M:N); adds or modifies uniqueness constraints, foreign key constraints, or check constraints; normalizes or denormalizes a model; introduces or modifies a read model (materialized view, projection, CQRS read side); changes ownership boundaries (who owns and writes this data); defines lifecycle states or status progressions; specifies data retention, archival, or deletion policies; or designs a schema that will be directly exposed to other services.

# Do Not Use When

Do not use this capability to mirror a UI form directly into a database table — forms reflect UX concerns; models reflect domain invariants. Do not use it to expose persistence tables as API contracts — use `dto-schema-design` and `api-contract-design`. Do not use it for query performance optimization on an existing schema — that is physical tuning; use `relational-database` or `nosql-database`. Do not use it to design migration scripts for existing data — use `data-migration-design`.

# Non-Negotiable Rules

- **Model invariants first, storage second.** Define what must always be true (invariants), what constitutes an invalid state, what transitions are allowed, and who owns each attribute — before choosing table structure, document structure, or index layout. Storage is a physical concern; invariants are a domain concern.
- **Every entity has a single owner.** No attribute is written by two services without a defined authority and sync protocol. Shared mutable state with no ownership is the root cause of data inconsistency at scale. Ownership is per-attribute, not just per-table.
- **Invalid states must be unrepresentable where feasible.** Use database constraints (NOT NULL, UNIQUE, CHECK, FOREIGN KEY), enumeration columns with allowlisted values, state machine enforcement (CHECK constraint on status with allowed transitions), and nullable semantics deliberately. A `status` column that can simultaneously have `started_at` populated and `status = 'pending'` is an invalid state that is fully representable — design it out.
- **Nullable fields encode lifecycle intent, not laziness.** A nullable column means "this attribute does not always exist for this entity." If it is nullable only because the value is not known at creation but becomes required later, that is a lifecycle state — model it as a state transition (status column), separate table, or temporal attribute with `created_at` / `filled_at` markers.
- **Query and write patterns drive physical design, not the reverse.** Before choosing normalization level, partition key, index strategy, or document embedding, list: the 3-5 most critical query patterns (read access patterns), the write rate and write pattern (append-only, update-heavy, time-series), the cardinality of each relationship, and the expected data volume. These determine whether normalization, denormalization, embedded documents, or materialized views are appropriate.
- **Migration risk is evaluated at design time.** Before finalizing a model, assess: can a column be added safely (nullable first)? can it be renamed without a dual-write phase? can it be dropped without affecting other services? Models designed without migration awareness become unmaintainable as the system evolves.
- **Persistence internals do not leak as contracts.** Table names, column names, foreign key IDs, internal surrogate keys, ORM join columns, and version/etag fields are implementation details. External APIs and inter-service contracts use DTOs with stable field names that evolve independently. Changes to persistence implementation must not silently break consumers.
- **Soft-delete is a product decision, not a default.** Soft-delete (`deleted_at`, `is_deleted`) introduces: query filter noise (every query must add `WHERE deleted_at IS NULL`), unique constraint interference, referential integrity complexity, audit log duplication, and GDPR "right to be forgotten" complications. Use it only when the business explicitly requires recoverable deletion or audit of deletions. Otherwise, hard-delete with proper archival strategy.
- **Aggregate boundaries define transaction scope.** Objects modified together in one business operation belong in the same aggregate. Objects that can be modified independently belong in separate aggregates. An overly large aggregate causes write contention; an overly small aggregate requires distributed transactions for business operations that should be atomic.

# Industry Benchmarks

Anchor against: **Domain-Driven Design (Eric Evans, 2003)** — Entity, Value Object, Aggregate, Repository, Domain Event; aggregate boundary as transaction boundary; ubiquitous language in model naming. **Domain-Driven Design Distilled (Vaughn Vernon, 2016)** — aggregate design rules; Cargo/Policy examples. **Designing Data-Intensive Applications (Kleppmann, 2017)** Ch. 2 (Data Models) and Ch. 3 (Storage and Retrieval) — document vs relational vs graph tradeoffs. **CQRS / Event Sourcing (Fowler, Young, Vernon)** — read model design, event stream as source of truth, projection rebuild. **Third Normal Form (3NF)** and **Boyce-Codd Normal Form (BCNF)** (Codd, 1972) — normalization for relational consistency. **Temporal Data and the Relational Model (Date, Darwen, Lorentzos)** — temporal attributes; bi-temporal modeling (valid time, transaction time). **GDPR Article 17** (Right to Erasure) — design for data deletion without breaking historical records. **HIPAA Safe Harbor** — de-identification rules affecting storage of PHI. **PCI DSS Requirement 3** — cardholder data storage minimization. **OWASP Secure Coding Practices** — parameterized queries; avoid dynamic SQL assembled from column names; no internal IDs in public-facing APIs. **Martin Fowler "Analysis Patterns"** — reusable domain models for accounts, parties, observations. **"The Data Model Resource Book" (Hay)** — canonical industry data models. **PostgreSQL Constraint Types** — `CHECK`, `UNIQUE`, `EXCLUDE`, `FOREIGN KEY DEFERRABLE` for constraint-enforced invariants. **JSON Schema Draft 2020-12** — document model validation.

### Storage Type Selection Matrix

| Storage type | Invariant enforcement | Query flexibility | Schema evolution | Pick when |
| --- | --- | --- | --- | --- |
| **Relational (PostgreSQL, MySQL)** | Strong (FK, CHECK, UNIQUE, transactions) | High (arbitrary joins, aggregations) | DDL migrations required | Structured data with relationships; ACID required; complex queries |
| **Document (MongoDB, DynamoDB, Firestore)** | Application-level only | By access pattern (embedded vs reference) | Schema-free but requires app discipline | Hierarchical / nested data; access-pattern-driven; flexible schema |
| **Time-series (TimescaleDB, InfluxDB, Cassandra)** | Weak (append-only usually) | Time-range; limited aggregation | Append-only; column add possible | Sensor data, metrics, events with time-based queries |
| **Graph (Neo4j, Amazon Neptune)** | Relationship-level constraints | Traversal; pattern matching | Node/edge label add | Social graphs, knowledge graphs, complex relationship traversal |
| **Key-value (Redis, DynamoDB simple)** | None (schema-free) | By key only | Key/value change | Session storage, cache, counters, simple lookup |
| **Wide-column (Cassandra, HBase)** | Partition-key uniqueness | Partition key + clustering key only | Column family add (online) | High-write time-series; geographically distributed writes |
| **Event store (EventStore, Kafka + compaction)** | Append-only; event ordering | Projection rebuilds | Append events; schema evolution via upcasting | Event-sourced aggregates; audit log; rebuild capability |

### Normalization vs Denormalization Decision Tree

```
Is the data read-heavy with complex joins across multiple entities?
├─ Yes + latency is critical → Consider denormalization or read model (materialized view / CQRS projection)
│   └─ Is the denormalized data authoritative or derived?
│       ├─ Derived → Use materialized view; define refresh interval and staleness tolerance
│       └─ Authoritative → Dual-write is dangerous; reconsider aggregate boundary instead
└─ No → Normalize to 3NF as baseline

Does the query join > 3 tables for every read of this entity?
├─ Yes → Evaluate: pre-join read model vs query optimization vs domain model split
└─ No → Stay normalized; add index

Is the relationship 1:few (< 20 items, always accessed together, same write owner)?
├─ Yes → Embed in document or use JSON column (PostgreSQL jsonb)
└─ No → Separate table with foreign key

Is the relationship M:N?
└─ Use explicit junction table with own primary key, created_at, and status — never an implicit join table
```

### State Machine Constraint Pattern

```sql
-- Model lifecycle states as a constrained enum
CREATE TYPE order_status AS ENUM ('draft', 'submitted', 'confirmed', 'shipped', 'delivered', 'cancelled');

-- Enforce valid transitions via check constraint (application validates; DB is safety net)
ALTER TABLE orders ADD CONSTRAINT order_status_not_null CHECK (status IS NOT NULL);

-- Enforce that shipped_at is only set when status = 'shipped' or later
ALTER TABLE orders ADD CONSTRAINT shipped_at_valid
  CHECK (shipped_at IS NULL OR status IN ('shipped', 'delivered'));

-- Enforce that cancelled_at is only set when status = 'cancelled'
ALTER TABLE orders ADD CONSTRAINT cancelled_at_valid
  CHECK (cancelled_at IS NULL OR status = 'cancelled');
```

Key principle: the database is the last line of defense for invariants. Application-layer-only enforcement fails under direct SQL access, migration scripts, or bugs.

### Data Ownership Boundary Map

| Boundary question | Rule |
| --- | --- |
| Who creates this record? | Only that service writes the `created_at` and surrogate key |
| Who updates `status`? | Single authority service; others subscribe to events |
| Who can delete? | Named owner + authorization gate; logged in audit table |
| Cross-service read | Exposed via API/event only; never via shared DB access |
| Shared DB (legacy) | Must define write-authority per column; read-only for consumers |
| External ID mapping | Separate cross-reference table owned by the integrating service |

# Selection Rules

Select this capability when **the shape, constraints, and lifecycle of stored data** are the primary decisions. Adjacent routing:

- Prefer `dto-schema-design` when the question is the serialized transfer object structure for APIs or events.
- Prefer `api-contract-design` when defining what clients see (vs what is stored).
- Prefer `data-migration-design` when the model is changing for existing stored data.
- Prefer `relational-database` for physical storage-engine specifics (index types, partitioning, vacuum, MVCC).
- Prefer `nosql-database` for physical document model specifics (embedding strategy, sharding, TTL, consistency settings).
- Prefer `domain-impact-modeler` when assessing how a model change propagates across bounded contexts.

# Risk Escalation Rules

Escalate when: the model stores regulated data (PII/PHI/PCI/PSD2 financial); the model is the source of truth for financial account balances, audit logs, or compliance records; data deletion is irreversible and violates GDPR/CCPA requirements; the aggregate boundary change requires distributed transactions across services that cannot be made atomic; the model is shared across microservices via direct DB access (dual-write, read replica coupling); the model change requires a large backfill (> 10M rows) with no approved migration plan; a foreign key removal would silently allow orphaned records; the model stores cryptographic material (key IDs, hashes, salts) without defined access control.

# Critical Details

The most expensive data model mistakes are invisible at design time and catastrophic at scale:

- **The NULL problem.** A `nullable` column can mean four different things: (1) "not yet known", (2) "not applicable", (3) "deleted/removed", (4) "explicitly set to empty". Each meaning implies different business logic and query behavior. Use separate boolean flags (`is_applicable`, `is_deleted`) or separate tables for different lifecycle meanings instead of overloading nullable semantics.
- **Surrogate vs natural keys.** Surrogate keys (UUID, auto-increment) are stable and safe for internal references. Natural keys (email, SSN, product code) change in the real world and should not be primary keys used as foreign key targets. Use surrogate keys as PK; store natural keys as unique-constrained columns.
- **UUID v4 vs UUID v7 for performance.** UUID v4 is random → causes B-tree index fragmentation at high insert rates. UUID v7 (draft RFC 9562) is time-ordered → insert locality; better index performance. For PostgreSQL at high insert rates, use `gen_random_uuid()` (v4) or a time-sortable ID (ULID, UUID v7) based on insert pattern.
- **Soft-delete + unique constraints.** `UNIQUE(email)` + `deleted_at IS NOT NULL` means a deleted user's email blocks re-registration. Solution: partial unique index `CREATE UNIQUE INDEX ON users(email) WHERE deleted_at IS NULL`.
- **Polymorphic associations.** A `comments` table with `commentable_type` + `commentable_id` cannot have a foreign key constraint. Referential integrity is lost. Prefer separate junction tables (`post_comments`, `video_comments`) with proper foreign keys.
- **Temporal modeling.** For "what was the value at time T?" use bi-temporal tables: `valid_from`, `valid_to` (business validity) + `created_at` (transaction time). Overwriting current values loses history. Use SCD Type 2 (insert new row, close old row's `valid_to`) for auditable temporal data.
- **JSON columns: flexibility vs constraint.** `jsonb` in PostgreSQL offers flexible schema but no column-level constraints, no foreign keys, no column statistics for the planner. Use for genuinely schema-variable data; never as a workaround for avoiding proper schema design.
- **N+1 query patterns.** A 1:N relationship where the application fetches the parent then loops to fetch each child is an N+1 pattern baked into the model. Design the model and access layer together; use eager loading (`JOIN`, `IN` clause, or dataloader pattern) for collection relationships.
- **Write amplification in denormalized models.** Denormalized copies of data (e.g., `username` copied to every post record) require updating every copy on change. At scale, write amplification outweighs read simplification. Prefer read-time joins or materialized views with explicit staleness tolerance.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `users` table with `json_data` column containing all variable fields | No constraints; application diverges; impossible to query or index; migration requires full table scan |
| `orders` table with 12 nullable columns, no status enum | Invalid states representable; NULL means 4 different things; bugs from overloaded nullability |
| Table name `user_accounts` in API response JSON | Persistence internals in contract; rename breaks all consumers |
| `status VARCHAR(255)` with no constraint | Any string is valid status; typos silently stored; application logic diverges |
| Comments with `commentable_type / commentable_id` (polymorphic) | No FK constraint; orphaned comments accumulate; cannot join efficiently |
| Soft-delete + UNIQUE(email) | Deleted user's email permanently blocks new registration unless partial index added |
| Service B reads Service A's database directly | Tight coupling; any schema change in A breaks B silently; no ownership boundary |
| UUID v4 as clustered PK at 100K inserts/s | B-tree fragmentation; index size 2× random; IO amplification at scale |

# Failure Modes

- Table designed from screen mockup; domain invariant `order must have at least one line item` not enforced; empty orders possible.
- Nullable overloaded: `completed_at IS NULL` means both "not started" and "cancelled" depending on undocumented convention; query logic branches diverge.
- Two services write to the same column with no authority rule; last-write-wins causes data loss during concurrent updates.
- `status` stored as `VARCHAR` with no constraint; typo `'shiped'` stored; dashboard aggregation silently drops 2% of orders.
- Soft-delete added without partial unique index; re-registration fails for deleted users; support tickets.
- Model ships without migration plan; column add requires NOT NULL DEFAULT on PG 10; outage during deployment.
- External API returns `user_id`, `table_name`, `db_schema` fields (persistence internals); API versioning required immediately after shipping.
- Aggregate boundary too large: `order` aggregate includes `customer`; write contention; deadlocks under concurrent order placement.
- Aggregate boundary too small: `order_item` is a separate aggregate; placing an order requires 2-phase commit; distributed transaction bug.
- Temporal query ("what was the price on 2025-01-01?") impossible because price column is overwritten in place; historical records lost.
- UUID v4 clustered PK with 200K inserts/s; index fragmentation grows; query performance degrades 3× over 6 months.

# Output Contract

Return a data model proposal with:

- `entities_or_documents` (per entity: name, table/collection, purpose, storage type)
- `ownership` (per entity/attribute: owning service, write authority, cross-service access protocol)
- `invariants` (per entity: rules that must always be true; invalid state description; enforcement: DB constraint vs application)
- `attributes` (per attribute: name, type, nullable, default, constraint, lifecycle meaning)
- `relationships` (per relationship: entity A, entity B, cardinality, foreign key strategy, nullability, referential action)
- `lifecycle_states` (per entity: valid states, allowed transitions, check constraint SQL)
- `query_patterns` (3-5 critical queries with access pattern, index strategy, estimated selectivity)
- `write_patterns` (write rate estimate, update-heavy vs append-only, concurrent write risk)
- `constraints` (UNIQUE, CHECK, FK, EXCLUDE constraints; partial index for soft-delete if used)
- `retention_and_deletion` (retention period, archival strategy, GDPR/CCPA deletion approach, audit log requirements)
- `migration_impact` (columns safe to add nullable-first, columns requiring dual-write, columns that are breaking)
- `read_models` (CQRS projections or materialized views: staleness tolerance, rebuild strategy)
- `contract_separation` (API-facing DTO names and fields vs internal table names; explicit mapping)
- `normalization_level` (3NF, BCNF, or justified denormalization with staleness policy)
- `open_decisions` (unresolved: aggregate boundary, ownership, temporal modeling approach)

# Quality Gate

The data model passes only when:

1. All domain invariants are stated; each is enforced at DB layer (constraint) or at minimum at service layer with documented rationale for not using DB constraint.
2. Every entity has a single named write-authority; cross-service access is via API/event not direct DB.
3. Nullable columns have explicit semantic meaning; no overloaded nullability.
4. All status/enum fields are constrained to valid values at the DB layer.
5. Query patterns are documented with index strategy; no obvious N+1 or full-table-scan pattern uncovered.
6. Migration impact is assessed; no single-step breaking DDL on hot tables.
7. Persistence internals (table names, column names, internal IDs) are not in the external API contract.
8. Lifecycle state machine has invalid-state constraints enforced at DB layer.
9. Retention and deletion policy is documented; GDPR/CCPA deletion is possible without breaking historical integrity.
10. Aggregate boundary matches transaction scope; no cross-aggregate atomicity without explicit distributed transaction strategy.

# Used By

- data-api-contract-changer
- domain-impact-modeler

# Handoff

Hand off to `data-migration-design` for migration planning on existing data; `dto-schema-design` for API transfer shapes; `api-contract-design` for client-visible behavior; `relational-database` for physical relational tuning; `nosql-database` for document model physical design; `domain-impact-modeler` for cross-context impact analysis.

# Completion Criteria

The capability is complete when **the data model encodes domain invariants with DB-level enforcement, supports known access patterns without emergency rewrites, has clear ownership per attribute, has a migration-safe evolution path, and cleanly separates persistence internals from API contracts** — and every invalid state that the business cares about is unrepresentable in the schema.
