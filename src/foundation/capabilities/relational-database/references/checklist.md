# Relational Database Checklist

- Name the physical tables, keys, tenant scope, relationship cardinality, null/unknown meaning, deletion behavior, and authoritative writers changed.
- Map each engine-enforceable invariant to its constraint and each contextual invariant to its owning application/domain boundary.
- Define foreign-key update/delete actions, conflict translation, and the losing concurrent path for uniqueness, reference, check, or version failures.
- Confirm the actual engine/version, deployed DDL, ORM mapping, connection settings, isolation, and replica routing used by the changed path.
- Tie each proposed index to a named query, distribution and plan evidence, write cost, and an `indexing-query-optimization` handoff when depth is needed.
- Classify physical changes by lock, rewrite, validation, mixed-version, reader or writer, recovery, and rollback impact, with execution assigned to `data-migration-design`.
- Prove relevant constraints and negative or concurrent outcomes with current schema inspection, tests, production-plan evidence, and lock, contention, and replica proof limits.
