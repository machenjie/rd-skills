# SQL Semantic Boundary Traps

This reference isolates SQL NULL, cardinality, constraint, transaction, precision, parameter, dialect, and DDL boundaries whose semantics vary with context.

## Decision Matrix

| SQL facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Predicates and three-valued logic | NULL sources, `UNKNOWN` handling, anti-join form, check semantics, and null-safe comparison | A predicate that passed non-NULL fixtures drops or admits rows after NULL appears |
| Joins and cardinality | Key relation, expected multiplicity, outer-join preservation, duplicate policy, order, and tie-breaker | A join multiplies rows or a filter turns an outer join into an inner join |
| Aggregates and windows | Empty input, NULL treatment, grouping key, frame, peer/tie behavior, numeric result type, and ordering | Totals, counts, ranks, or running values change at empty, duplicate, or boundary rows |
| Constraints and upserts | Invariant owner, NULL uniqueness semantics, deferrability, conflict target, returned row, and concurrent outcome | A precheck or upsert silently permits a duplicate, overwrites a newer value, or returns the wrong row |
| Transactions and locks | Isolation, snapshot/read source, lock class and order, retryable failures, read-your-writes, and cancellation | Sequential tests pass while concurrent executions lose, duplicate, block, or read stale state |
| Numeric and temporal types | Units, precision, scale, rounding, instant/local meaning, timezone, driver mapping, and conversion boundaries | Storage or coercion changes amount, ordering, equality, or represented time |
| Dialect and DDL | Engine/version, transactional DDL, lock/rewrite behavior, default/backfill, collation, generated SQL, and coexistence | Syntax succeeds while deployment locks data, rewrites rows, or changes semantics across versions |

## Decision Limits

- The selected engine and version are authoritative for NULL uniqueness, isolation, locking, DDL, type, collation, and plan behavior.
- A plan or timing result applies to its query, parameters, statistics, data shape, cache state, and environment; future distributions can select another path.
- Value binding does not parameterize identifiers, operators, order clauses, or arbitrary SQL structure; those choices need a closed mapping.
- A database constraint establishes the invariant for writes that reach that constraint in the deployed schema and transaction model.
- Migration sequencing, deep index design, distributed consistency, and product money or timezone policy remain with their specialist owners.
- Current fixtures and checks cover named dialects and data shapes; untested NULL, concurrency, migration-skew, replica, or engine-version paths remain risks.
