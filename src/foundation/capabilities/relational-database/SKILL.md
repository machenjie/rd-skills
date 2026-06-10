---
name: relational-database
description: Selects and designs relational storage when transactions, integrity, consistency, constraints, and complex SQL queries matter.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "45"
changeforge_version: 0.1.0
---

# Mission

**Design relational database schemas, constraints, transaction boundaries, index strategies, and migration plans so that transactional invariants are enforced at the database layer, query performance is predictable, and schema migrations are deployable without downtime or data loss** — making the relational layer a correctness boundary, not just a storage mechanism.

# When To Use

Use this capability when: a new entity, relationship, or data domain requires SQL tables, foreign keys, unique constraints, or check constraints; a business invariant must be enforced across multiple rows or tables atomically; a query involves joins, aggregations, window functions, or complex filtering where query plan analysis is needed; a schema migration affects tables with high row counts, high write throughput, or critical business data (financial records, audit logs, compliance data); or a performance problem in the data layer requires index redesign, query plan analysis, or normalization review.

# Do Not Use When

Do not use this capability to: default every new entity to SQL without an access-pattern analysis (do access-pattern modeling first; many high-volume, key-access-only patterns belong in NoSQL — see `nosql-database`); design a relational schema and then expose it directly as an API contract (API shape must evolve independently — see `dto-schema-design`); resolve caching, search, or event-stream requirements (use `cache-design`, `search-analytics-design`, `message-queue-design` respectively); or optimize a slow query without first confirming the schema design and index strategy (use `indexing-query-optimization` for query-level optimization).

# Non-Negotiable Rules

- **Encode invariants as database constraints, not only application code.** Unique constraints, foreign key constraints, check constraints, and NOT NULL are the only invariant enforcers that cannot be bypassed by a second writer, a migration script, a background job, or a direct database connection. Rule: if an invariant is critical (uniqueness of email address, non-negative account balance, valid status transitions), it must exist as a database constraint in addition to application-level validation. Application-only enforcement is a single-writer illusion.
- **Define transaction scope, isolation level, and conflict handling before writing concurrent update logic.** The default isolation level (READ COMMITTED in PostgreSQL; REPEATABLE READ in MySQL) determines what concurrent writers can see and overwrite. Rule: for any write path that protects a financial balance, an inventory count, a booking slot, or any other numeric or state invariant — explicitly choose the isolation level, lock strategy (SELECT ... FOR UPDATE, SERIALIZABLE), and conflict handling (retry, fail-fast, compensating transaction). "The ORM handles it" is not an isolation level.
- **Design indexes from query predicates, not from guesswork.** Every index must be justified by a specific query: the WHERE clause columns (selectivity matters — high-cardinality columns first), the JOIN key, the ORDER BY column, and whether a covering index eliminates a table scan. Rule: for every new index, document: the query it supports, the estimated predicate selectivity, the table size, the expected query frequency, and the write overhead (INSERT/UPDATE/DELETE cost increases with every index).
- **Schema migrations must be staged for production safety.** On tables with > 1M rows, a migration that rewrites or locks the table causes downtime. Rule: use the expand-contract pattern — (1) Expand: add the new column (nullable, no DEFAULT that rewrites all rows, no NOT NULL yet); deploy application code that writes to both old and new; (2) Migrate: backfill existing rows in batches with LIMIT and SLEEP to avoid lock contention; (3) Contract: add NOT NULL constraint (or drop old column) after all rows are migrated and old code is removed. For column renames: add new column → backfill → update all writers → drop old column. Never rename directly.
- **Separate the internal relational schema from external API contracts.** A table column rename must never require an API consumer change. The API DTO is mapped from the relational record in the application layer (see `dto-schema-design` and `repository-persistence`). Returning ORM entities directly from API handlers couples the external contract to the internal schema and makes column rename or normalization a breaking API change.
- **Avoid N+1 query patterns at the schema and repository design stage.** An N+1 query (fetching 1 parent row then N child rows in a loop) is often invisible in development (small datasets) and catastrophic in production (large datasets). Rule: identify any `findAll()` + loop pattern in repository or service code; replace with a JOIN-based or eager-load query; verify with EXPLAIN ANALYZE in development before shipping.

# Industry Benchmarks

Anchor against: **PostgreSQL documentation** — MVCC model; EXPLAIN ANALYZE; index types (B-tree, GIN, GiST, BRIN); autovacuum and bloat; LISTEN/NOTIFY; pg_stat_statements for slow query identification. **MySQL/InnoDB documentation** — REPEATABLE READ default; gap locks; deadlock detection; online DDL (ALTER TABLE ALGORITHM=INPLACE/INSTANT). **C.J. Date "Database in Depth" / "An Introduction to Database Systems"** — relational integrity; referential integrity; entity integrity; domain integrity. **Martin Kleppmann "Designing Data-Intensive Applications" (2017)** — isolation levels (read committed, snapshot, serializable); lost update problem; write skew; phantom reads; optimistic vs pessimistic concurrency. **Percona / GitHub Engineering blog** — online schema migration (gh-ost for MySQL; pg_repack for PostgreSQL); zero-downtime migration practice. **OWASP SQL Injection Prevention** — parameterized queries only; never dynamic string concatenation for SQL; input validation at application boundary. **Joe Celko "SQL for Smarties"** — window functions, hierarchical queries, set-based thinking vs row-by-row loops.

### Storage Technology Decision Matrix

| Requirement | Relational (PostgreSQL/MySQL) | NoSQL (Document) | NoSQL (Key-Value) | Time-Series |
| --- | --- | --- | --- | --- |
| Multi-entity atomic transactions | ✅ ACID | ⚠️ limited (MongoDB multi-doc txn) | ❌ | ❌ |
| Complex joins across 3+ entities | ✅ | ❌ | ❌ | ❌ |
| Uniqueness across rows | ✅ UNIQUE constraint | ⚠️ application-enforced | ❌ | ❌ |
| High write throughput (> 50k writes/s) | ⚠️ requires sharding | ✅ | ✅ | ✅ |
| Key-only access (get by ID) | ✅ (with index) | ✅ | ✅ | N/A |
| Flexible schema / nested docs | ⚠️ JSONB (PostgreSQL) | ✅ | ❌ | ❌ |
| Time-ordered data with retention | ⚠️ partitioned tables | ❌ | ❌ | ✅ |
| Full-text search | ⚠️ pg_trgm / tsvector | ⚠️ Atlas search | ❌ | ❌ |

### Migration Risk Classification

```
Migration Risk Assessment:

1. Table row count:
   < 100k rows    → LOW: standard ALTER TABLE acceptable
   100k–10M rows  → MEDIUM: test migration time in staging; consider batched backfill
   > 10M rows     → HIGH: online migration tool required (gh-ost / pg_repack / Flyway batched)

2. Migration operation type:
   ADD COLUMN nullable (no DEFAULT)    → LOW: instant metadata-only in PostgreSQL
   ADD COLUMN NOT NULL with DEFAULT    → HIGH: rewrites all rows (PostgreSQL < 11); use expand-contract
   DROP COLUMN                         → MEDIUM: mark soft-deleted first; confirm no readers
   RENAME COLUMN                       → HIGH: add new + backfill + drop old (never direct rename)
   ADD INDEX (CONCURRENTLY in PG)      → LOW/MEDIUM: CONCURRENTLY avoids table lock
   DROP INDEX                          → LOW
   ADD FOREIGN KEY                     → MEDIUM: requires full table scan; use NOT VALID + VALIDATE CONSTRAINT
   ADD UNIQUE CONSTRAINT               → HIGH: full table scan + lock; add as unique index CONCURRENTLY first

3. Expand-Contract pattern steps:
   Phase 1 (Expand):  Add new column/table; deploy code that writes to both old+new
   Phase 2 (Migrate): Batch backfill existing rows (LIMIT 1000 + SLEEP 10ms between batches)
   Phase 3 (Clean):   Deploy code that reads only new; drop old column/table
   Each phase is a separate deployment with validation checkpoint.

4. Rollback plan per phase:
   Phase 1: Drop new column (no data loss; old code still uses old column)
   Phase 2: Stop backfill; Phase 1 rollback still possible
   Phase 3: Requires restore from backup if old column dropped; plan forward-fix instead
```

### Transaction Isolation Decision Tree

```
Is this write protecting a shared numeric value (balance, count, inventory)?
  YES → Use SELECT ... FOR UPDATE (pessimistic) or SERIALIZABLE isolation
  NO  → Continue

Can two concurrent writers produce inconsistent state (write skew, double-booking)?
  YES → SERIALIZABLE isolation (PostgreSQL SSI) or explicit advisory locks
  NO  → Continue

Do you need to read your own uncommitted writes within the transaction?
  N/A in standard isolation → READ COMMITTED is sufficient for most reads

Default recommendation by pattern:
  Simple insert (no conflict) → READ COMMITTED (default)
  Upsert / idempotent write   → READ COMMITTED + ON CONFLICT DO UPDATE
  Balance / inventory update  → REPEATABLE READ + SELECT FOR UPDATE
  Cross-table invariant check → SERIALIZABLE
  Bulk import / batch job     → READ COMMITTED + retry on deadlock
```

# Selection Rules

Select this capability when **transactional correctness, relational integrity, or schema migration safety is the primary concern**. Route elsewhere when: `nosql-database` is primary (the access pattern is key-lookup or document-centric with no multi-entity transactions); `transaction-consistency` is primary (designing the isolation level and locking strategy in depth for an existing schema); `indexing-query-optimization` is primary (a specific slow query needs EXPLAIN ANALYZE and index tuning — the schema design is already settled); `data-migration-design` is primary (the migration sequencing and deployment order for a complex schema change); `data-model-design` is primary (the conceptual entity model and relationship design, before SQL DDL is written).

# Risk Escalation Rules

Escalate when: a migration touches a table with > 10M rows or > 50k writes/s (requires online migration tool, staging test, and explicit rollback plan before production); a transaction design involves financial balances, inventory counts, or double-entry accounting (requires isolation level review and a reconciliation test); a migration drops a column or table (requires confirmation that no application code, reporting query, or ETL pipeline reads the dropped structure — grep all consumers before dropping); a new schema introduces multi-tenant data (requires row-level security or tenant_id predicate on every query — no shared-tenant data access); a schema stores PII or regulated data (requires encryption-at-rest verification, retention policy, and access control review before table creation).

# Critical Details

- **NOT NULL constraints must be added safely on large tables.** In PostgreSQL ≥ 14, `ALTER TABLE ADD COLUMN NOT NULL DEFAULT 'x'` is instant (stored as catalog metadata, not a row rewrite) for new columns. For existing nullable columns being made NOT NULL: (1) add a CHECK constraint with NOT VALID (fast); (2) backfill all NULL rows; (3) validate constraint (`ALTER TABLE VALIDATE CONSTRAINT`) — this takes a ShareUpdateExclusiveLock, not AccessExclusiveLock, so reads continue.
- **Foreign key constraints should be added with NOT VALID first on large tables.** `ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;` skips the full table scan for existing rows. Then: `ALTER TABLE orders VALIDATE CONSTRAINT fk_user;` validates existing rows with a weaker lock.
- **EXPLAIN ANALYZE must be run against representative data, not empty tables.** An index that the query planner uses on a 1,000-row development table may be ignored (seq scan chosen) on a 50M-row production table, or vice versa. Always test with EXPLAIN ANALYZE against a production-scale dataset (from anonymized backup or generated data at production cardinality).
- **Deadlock prevention follows a consistent locking order.** When multiple transactions acquire locks on multiple tables, the lock acquisition order must be consistent across all transactions. Example: if Transaction A locks `orders` then `order_items`, Transaction B must also lock `orders` then `order_items` — never the reverse. Inconsistent lock order is the primary cause of deadlocks.
- **Soft deletes require explicit filtering on every query.** If a `deleted_at` column is used instead of physical DELETE: every query that should not return soft-deleted rows must have `WHERE deleted_at IS NULL`. Missing this filter on one query path causes ghost-record leaks. Consider PostgreSQL row-level security policies or a view to enforce the filter uniformly.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Uniqueness enforced only in application: `if (exists(email)) throw` | Race condition: two concurrent requests both pass the check and both insert; duplicate records created | `UNIQUE INDEX ON users(email)` at database level |
| `ALTER TABLE ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT ''` on 50M-row table (PG < 11) | Full table rewrite; table locked for minutes; production outage | Expand-contract: add nullable → backfill → add NOT NULL constraint NOT VALID → validate |
| Returning ORM entity from REST endpoint: `res.json(userRecord)` | Schema column rename requires API change; password_hash accidentally exposed if ORM maps all columns | Map to DTO explicitly; never expose ORM entities as API response |
| `SELECT * FROM orders` + loop calling `getUser(order.user_id)` | N+1 queries: 1 + N database round-trips for N orders; 1,000 orders = 1,001 queries | `SELECT orders.*, users.* FROM orders JOIN users ON orders.user_id = users.id` |
| Transaction reads balance, computes new balance, writes — no lock | Lost update under concurrent writes: two transactions both read $100, both subtract $10, both write $90; balance should be $80 | `BEGIN; SELECT balance FROM accounts WHERE id=1 FOR UPDATE; UPDATE ...; COMMIT;` |
| Foreign key added without index on FK column | Every DELETE on parent table causes full child table scan to check referential integrity; severe write performance degradation | Create index on FK column before adding constraint |

# Failure Modes

- Uniqueness invariant enforced only in application code — concurrent insert requests create duplicate email records; discovered only when users report login failures.
- `ALTER TABLE RENAME COLUMN` deployed on a 30M-row production table — full table lock — 4-minute downtime.
- Schema migration drops a column — an ETL pipeline that reads that column starts producing NULL values in the data warehouse; data quality incident.
- Financial balance updated with READ COMMITTED isolation — lost update problem — two concurrent withdrawals both succeed; account balance goes negative.
- EXPLAIN ANALYZE not run before deployment — a query that seq-scans a 10M-row table under load — 30-second queries — timeout cascade.
- PII stored in a new table without encryption-at-rest verification — compliance audit finding.

# Output Contract

Return a relational database design with:

- `entity_and_table_design` (table names, column names, types, constraints: PK, FK, UNIQUE, CHECK, NOT NULL)
- `relationship_model` (one-to-many, many-to-many join tables, cascade rules)
- `invariant_enforcement` (which invariants are enforced at DB level vs application level; justification)
- `transaction_scope` (which operations are atomic; isolation level chosen; locking strategy)
- `index_plan` (per index: supporting query, predicate columns, estimated selectivity, write cost assessment)
- `migration_plan` (expand-contract phases; risk classification; estimated migration time; lock type; rollback per phase)
- `query_plan_review` (EXPLAIN ANALYZE output for critical queries against representative data)
- `api_decoupling` (confirmation that internal schema is not exposed as external contract)
- `observability` (slow query monitoring: pg_stat_statements; lock monitoring; vacuum monitoring)
- `tests` (integration tests: constraint enforcement, transaction isolation, not-found behavior, soft-delete filter)

# Evidence Contract

Close this capability only with relational-boundary evidence:

- **Boundaries inspected:** tables, constraints, indexes, transaction scope, isolation level, migration phases, API mapping boundary, query plans, and PII/retention controls.
- **Validation evidence:** migration dry-run or staging output, rollback or forward-fix proof, EXPLAIN ANALYZE for critical queries, constraint/isolation integration tests, and consumer scan for dropped/renamed columns.
- **What evidence proves:** relational invariants are enforced at the database boundary, critical queries have a justified plan, and migration phases can be deployed without known lock or compatibility break.
- **What evidence does not prove:** production cardinality, lock timing, replica lag, or ETL/reporting compatibility unless validated against representative data and consumers.
- **Residual risk and handoff:** name any untested table size, long-running lock, consumer scan gap, or rollback limit; hand off to `data-migration-design`, `transaction-consistency`, or `indexing-query-optimization` when deeper review remains open.

# Quality Gate

The relational design is complete only when:

1. Every critical invariant has a database constraint (not only application code).
2. Transaction scope, isolation level, and locking strategy are explicit for all concurrent write paths.
3. Every index is justified by a specific query with predicate and selectivity analysis.
4. Schema migration is risk-classified; expand-contract plan exists for HIGH/MEDIUM risk.
5. EXPLAIN ANALYZE is reviewed against representative data for all critical queries.
6. No ORM entity is returned directly as an API response.
7. Foreign key columns are indexed.
8. Soft-delete filter is applied uniformly (RLS policy or query convention).
9. PII and regulated data fields have encryption and retention policy noted.
10. Integration tests cover: constraint enforcement, isolation behavior, migration rollback.

# Used By

- data-middleware-change-builder
- data-api-contract-changer

# Handoff

Hand off to `data-model-design` for conceptual entity modeling; `data-migration-design` for migration sequencing and deployment ordering; `transaction-consistency` for isolation level deep-dives; `indexing-query-optimization` for slow query tuning; `repository-persistence` for application-layer persistence boundary design.

# Completion Criteria

The capability is complete when **the relational schema enforces all critical invariants at the database layer, transaction behavior under concurrent writes is explicit and tested, migrations are staged for zero-downtime deployment, and the internal schema is isolated from the external API contract**.
