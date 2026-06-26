# Relational Database Benchmarks And Patterns

Use this reference when the capability output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, evidence, output, and gates.

## Benchmark Anchors

- PostgreSQL: MVCC, `EXPLAIN (ANALYZE, BUFFERS)`, B-tree/GIN/GiST/BRIN, partial indexes, `NOT VALID` constraints, `CREATE INDEX CONCURRENTLY`, autovacuum, bloat, `pg_stat_statements`, and `pg_stat_user_indexes`.
- MySQL/InnoDB: `REPEATABLE READ`, gap locks, deadlock detection, online DDL with `ALGORITHM=INPLACE` or `INSTANT`, metadata-lock behavior, and `performance_schema`.
- Relational integrity: entity integrity, referential integrity, domain integrity, and set-based SQL design.
- Designing Data-Intensive Applications: isolation anomalies, lost update, write skew, phantom reads, optimistic and pessimistic concurrency.
- Online migration practice: expand/migrate/contract, `gh-ost`, `pt-online-schema-change`, `pg_repack`, batched backfills, and rollback tiering.
- OWASP SQL Injection Prevention: parameterized SQL or ORM parameter binding only; dynamic string concatenation is not acceptable.

## Storage Fit Matrix

| Requirement | Relational fit | Handoff or caution |
| --- | --- | --- |
| Multi-entity atomic transaction | Strong fit: ACID local transaction | Use `transaction-consistency` for isolation depth. |
| Foreign-key and uniqueness invariants | Strong fit: FK, UNIQUE, CHECK, NOT NULL | Prefer DB constraints over application-only checks. |
| Complex joins, reporting filters, window functions | Strong fit when query plans are proven | Use `indexing-query-optimization` for concrete slow paths. |
| Key-only high-scale access | Possible but maybe not ideal | Compare with `nosql-database` and cache/search alternatives. |
| Flexible nested payloads | Possible with JSON/JSONB | Do not hide required schema/versioning inside blobs. |
| Full-text relevance or faceting | Limited native support | Hand off to `search-analytics-design` when relevance is primary. |

## Migration Risk Classes

| Change | Default risk | Required evidence |
| --- | --- | --- |
| Add nullable column without default | Low | Old/new code compatibility and rollback-as-ignore/drop. |
| Add NOT NULL/default to existing large table | High | Expand/migrate/contract, lock class, backfill, validation. |
| Rename/drop column or table | High | Current readers/writers/report consumers, telemetry zero-use, rollback tier. |
| Add FK/check constraint on large table | Medium | `NOT VALID` then validation where supported, violation scan. |
| Add unique constraint | High | Duplicate scan, unique index build plan, conflict behavior. |
| Add/drop index on hot table | Medium/high | Online build/drop, usage evidence, write-cost estimate, rollback. |

## Transaction And Isolation Patterns

| Pattern | Baseline decision | Validation focus |
| --- | --- | --- |
| Simple insert with constraint | Read committed plus constraint handling | Duplicate/conflict test and safe error translation. |
| Upsert or idempotent write | Read committed plus `ON CONFLICT`/equivalent | Idempotency key scope and retry behavior. |
| Balance, inventory, booking slot | Pessimistic lock or serializable transaction | Concurrent write test and lock timeout behavior. |
| Cross-table invariant | Serializable or explicit locking order | Write-skew prevention and deadlock retry path. |
| Remote side effect plus DB write | Local transaction plus outbox/intent state | No remote call while DB lock is held. |

## Constraint And Query Patterns

- Enforce critical invariants twice: application validation for user feedback, database constraint for correctness.
- Index every foreign-key column used by parent deletes/updates or joins; otherwise referential checks can scan child tables.
- Pair soft deletes with RLS, views, scoped repositories, or enforced query conventions so `deleted_at IS NULL` is not optional.
- Treat ORM-generated SQL as source evidence only after inspecting generated SQL or a representative query log.
- Reject direct ORM entity exposure through APIs; map schema records into DTOs at repository/application boundaries.
- Confirm parameter binding for all user-influenced values, including filters, sort keys, dynamic table/column choices, and report builders.

## Graph, Memory, And Trajectory Coupling

Repository graph, project memory, and prior execution can suggest tables, readers, migrations, slow queries, and fragile patterns, but they do not prove relational safety. Before using that evidence:

- Confirm current schema definitions, migrations, repository methods, DTO mappers, generated clients, reports/jobs, and tests.
- Check whether "no readers", "safe DDL", "already indexed", "backfill complete", or "tenant filter exists" claims are fresh.
- Mark claims accepted, rejected, stale, or not verified; do not silently promote memory to evidence.
- Map every accepted claim to a validation command, SQL/query check, source path, telemetry artifact, or residual risk.

## Validation Checklist

- Schema: constraints, nullability, FK/index pairing, tenant/RLS/soft-delete policy, and API DTO decoupling inspected.
- Queries: SQL/ORM call site, filters, joins, sort, pagination, expected cardinality, and existing indexes inspected.
- Plans: `EXPLAIN`/plan evidence uses representative data or clearly states not-verified production limits.
- Migrations: row/write volume, lock class, EMC phases, backfill/checkpoint, validation queries, rollback tier, and restore limits named.
- Security/privacy: parameterized SQL, object/tenant filter, sensitive data classification, retention/encryption, and logging redaction noted.
- Tests: constraints, isolation/concurrency, repository mapping, migration rollback, soft-delete/tenant filter, and failure translation mapped to validators.
- Handoff: unresolved data model, API contract, transaction, indexing, migration, security, reliability, release, or test work has an owner.
