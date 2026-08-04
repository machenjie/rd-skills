---
name: relational-database
description: "`task-agent`: use when physical relational schema or database-enforced integrity changes; skip conceptual-model, repository-only, or unchanged relational-storage work."
---

# relational-database

## Registry Trigger

**Use when**

- design physical relational tables keys relationships constraints and database-enforced integrity

**Do not use when**

- only the conceptual model, repository mapping, query tuning, or migration execution changes
- no task-local relational database decision is required

## Skill Role

Define physical relational representation, database-enforceable integrity, engine semantics, and compatibility boundaries. Exclude business meaning, adapter mapping, transaction protocols, deep optimization, and migration execution.

## High-Value Rules

- Place each invariant at the strongest authority that can express it under concurrent writers.
- Use a database constraint as the final authority for an engine-expressible predicate reachable through concurrent writer paths.
- Treat application validation as feedback rather than race-safe authority for such predicates.
- Define key, relationship, and lifecycle semantics before DDL: identity stability, tenant scope, composite uniqueness, null versus absent meaning, foreign-key update or delete behavior, soft deletion, history, and orphan handling. Physical convenience cannot invent business meaning.
- Treat constraint conflicts as expected concurrent outcomes. Map uniqueness, reference, check, or version conflicts into stable domain failures, and prove the losing path preserves required failure atomicity; a read-then-write precheck alone is race-prone.
- Name the anomaly before selecting isolation, locks, or versions from effective engine, connection, replica, and retry semantics.
- Map proposed indexes to named query access characteristics, data distribution, and mutation cost without assuming plan optimality.
- Before a physical schema change, classify engine-specific lock, rewrite, validation, mixed-version, reader/writer, recovery, and rollback consequences. Route rollout and backfill mechanics to `data-migration-design` rather than prescribing a universal DDL recipe.

## Anti-Patterns

- Assuming ORM declarations or framework defaults prove deployed constraints, isolation, autocommit, generated SQL, or replica-visible behavior.
- Omitting tenant scope, null semantics, delete action, or conflict translation from a uniqueness or relationship rule.
- Treating a vendor/version-specific DDL shortcut, local row count, or development execution plan as production-safety proof.

## Stop Conditions

Stop when invariant authority or writers, actual engine/version/configuration, tenant or deletion semantics, or material DDL/plan/replica evidence is unknown and could change correctness. Repository inspection and deterministic tests prove inspected definitions and interleavings, not production contention, plan stability, lock duration, or replica lag.

## Output Contract

- Physical relational decision naming tables and keys, enforceable constraints, conflict and replica semantics, query beneficiaries, and transaction/index/migration handoffs.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Constraint isolation index replica or physical-evolution mechanisms remain unresolved | Current engine schema workload and writer evidence select one bounded mechanism | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Change affects keys constraints conflicts isolation replicas indexes tenant scope or physical evolution | No physical relational integrity or representation decision changes | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Constraint conflict isolation replica index or DDL-safety claims need fresh proof | Current schema configuration plans queries and tests prove each bounded claim | task-agent | evidence-record, proof-limit, residual-risk |
