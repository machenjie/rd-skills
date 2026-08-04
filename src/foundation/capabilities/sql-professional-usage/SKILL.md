---
name: sql-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when SQL changes affect NULL, cardinality, constraints, locks, precision, or dialect semantics; skip tool-only work."
---

# sql-professional-usage

## Registry Trigger

**Use when**

- SQL or generated-query changes can alter NULL and three-valued logic, row cardinality, constraints, transaction or lock behavior, precision, ordering, or dialect semantics.
- Query or DDL behavior needs compatibility across data shapes, application versions, database versions, or migration phases.

**Do not use when**

- The open decision is datastore selection, domain modeling, ORM structure, deep plan tuning, transaction protocol, or migration orchestration without a SQL-specific semantic question.
- No SQL text, generated SQL, schema, constraint, database type, transaction, or engine behavior changes.

## Skill Role

Protect SQL predicate and cardinality semantics, database invariants, parameter boundaries, numeric and temporal representation, dialect behavior, and SQL-visible compatibility.

## High-Value Rules

- Model predicates as `TRUE`, `FALSE`, or `UNKNOWN` across filters, joins, constraints, aggregates, and ordering.
- State row cardinality and multiplicity before joins, aggregation, windows, pagination, or upserts.
- Define deterministic tie-breakers for stable paging and first/last choices.
- Encode race-sensitive invariants in database constraints when the engine can own them.
- Declare transaction boundaries, isolation assumptions, lock order, retry class, read source, and visibility.
- Define units, precision, scale, rounding, instant/local meaning, timezone conversion, and driver representation.
- Parameter-bind external data values; map dynamic identifiers through a closed choice.
- Return a SQL semantic decision grounded in selected-engine/version verification, inspected evidence, and residual risk even when no Reference loads.

## Anti-Patterns

- A result from tiny development data is treated as proof of cardinality, plan stability, lock behavior, or production cost.
- `NOT IN`, an outer-join filter, an aggregate, or a uniqueness rule silently changes meaning when NULL or duplicate rows appear.
- `DISTINCT`, `COALESCE`, implicit casts, or floating-point storage hides an unresolved join, missing-value, type, precision, or consumer-contract defect.
- A fixed row threshold or engine-specific online-DDL recipe is applied without the current engine, version, data shape, lock behavior, and release path.

## Stop Conditions

- Route transactions, migrations, plans, indexes, and repositories to their specialist owners.
- Route public contracts, security, money, and timezone behavior to their specialist owners.

## Output Contract

- SQL semantic decision with NULL cardinality constraints transactions locks precision parameter dialect migration risks and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | SQL change crosses NULL cardinality constraint transaction precision parameter dialect or DDL boundary whose semantics remain unclear | Current SQL row contracts engine behavior and focused fixtures settle the changed boundary | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
