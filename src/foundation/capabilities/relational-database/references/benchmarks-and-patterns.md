# Relational Database Decision Patterns

Load this reference when relational storage fit, constraint authority, replica visibility, or physical-change mechanics leave multiple designs viable. Do not load it when the engine, invariant boundary, and adjacent owner already determine the physical design.

## Decision Boundaries

| Surface | Current evidence needed | Decision boundary |
| --- | --- | --- |
| Relational fit | Named invariants, relationship queries, writer set, atomicity need, and rejected simpler stores | Keep storage-fit and physical-integrity choice here; `data-model-design` owns business meaning. |
| Constraint authority | Predicate, writer reachability, null/tenant scope, conflict behavior, and engine support | Keep engine-enforceable integrity here; route contextual policy to its domain owner. |
| Concurrent update | Target anomaly, rows touched, effective isolation, replica routing, and partial-failure consequence | Record the relational facts here; route mechanism and retry depth to `transaction-consistency`. |
| Query or index | Named caller, predicates, joins, ordering, distribution, plan, and write cost | Route concrete plan/index selection to `indexing-query-optimization`. |
| DDL or backfill | Actual engine/version, lock/rewrite class, mixed-code window, data volume, recovery, and rollback | Route deployment sequence and execution to `data-migration-design`. |
| Repository mapping | Record/domain mapping, loading semantics, error translation, and unit-of-work owner | Route adapter behavior to `repository-persistence`. |

## Easy-To-Miss Relational Failures

- Confirm how the actual engine treats nulls in unique constraints; a uniqueness rule may need a composite, partial, generated, or application-plus-database design.
- Include tenant or parent scope in keys and references when identity is scoped. A globally unique surrogate key does not by itself protect cross-tenant association.
- Define foreign-key update/delete actions, cascade fan-out, cycles, soft-deleted parents, historical rows, and orphan policy before relying on referential integrity.
- Treat an application precheck as feedback. The database conflict path remains necessary when concurrent writers can pass the same check.
- For replica reads after a write, name read-your-writes, lag, fallback-to-primary, and user-visible stale behavior; the primary commit does not prove replica visibility.
- Keep defaults, generated values, timestamps, collation, timezone, and precision under one named authority, and verify round-trip behavior at repository and contract boundaries.

## Evidence Limits

Current DDL, ORM mappings, query plans, fixtures, and deterministic concurrency tests can prove inspected definitions and selected interleavings. They do not prove production plan stability, lock duration, contention, replica lag, restore behavior, or undiscovered writers; mark those limits and name the owner or validation needed.
