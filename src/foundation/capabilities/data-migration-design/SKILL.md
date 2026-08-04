---
name: data-migration-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when migration, backfill, deployment order, rollback, or live-data safety needs design; skip when no data migration exists."
---

# data-migration-design

## Registry Trigger

**Use when**

- design schema migration data backfill rollback validation and deployment ordering

**Do not use when**

- no task-local data migration design decision is required

## Skill Role

Define data-state transitions, mixed-version compatibility, live-writer coordination, backfill behavior, resumability, validation, rollback or forward repair, and completion evidence. Exclude business-rule ownership and production operation.

## High-Value Rules

- **Model source and target state before sequencing.** Name authoritative fields, invariants, volumes, writers, readers, derived data, constraints, and invalid or ambiguous source states that influence conversion.
- **Design for mixed-version coexistence.** Select expand, bridge, dual-read or write, versioning, or coordinated transition from observed deployment skew and consumer control; avoid a fixed phase count detached from the actual compatibility boundary.
- **Coordinate live writes with backfill.** Define writer authority, ordering, conflict resolution, capture point, replay, and cutover so late or concurrent updates cannot be overwritten or counted twice.
- **Make execution resumable and bounded.** Use stable identity, checkpoints, idempotent conversion, controlled batching, pacing, cancellation, and restart semantics derived from current capacity and lock or log impact.
- **Validate business meaning, not row movement alone.** Compare source and target counts plus domain invariants, null and exception classes, aggregates, relationships, samples, and consumer reads with explicit tolerance authority.
- **State rollback and forward-repair limits.** Identify irreversible transformations, data written by new code, old-reader limits, backup dependencies, reconciliation, and the last safe exposure or cutover point.
- **Define evidence-based completion.** Tie progress, errors, lag, reconciliation, and cleanup to queryable evidence and accountable owners; remove old paths only after current consumer and data evidence satisfies the exit condition.

## Anti-Patterns

- Couple schema change, full backfill, consumer cutover, and destructive cleanup into one irreversible mutation.
- Treat successful statements, copied row counts, or absence of errors as proof that business invariants survived.
- Retry non-idempotent conversion blindly or let backfill and live writers race without an authority rule.

## Stop Conditions

Escalate when authoritative state or writers are unknown, destructive change lacks recoverability evidence, mixed-version behavior is unsafe, or concurrent-write ordering is unresolved. Also escalate when conversion is not resumable, validation cannot detect semantic loss, or regulated, financial, identity, or audit data lacks an accountable owner.

## Output Contract

- migration decision with source and target state, compatibility sequence, writer and backfill coordination, resumability, validation evidence, rollback limits, completion condition, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Migration phases, backfill, cutover, or rollback tiers remain open | No schema, data, or mixed-version transition changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Migration spans locks, checkpoints, dual operation, or irreversible cleanup | An additive metadata change needs no data movement | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Safety claims require fresh dry runs, counts, or restore rehearsal | No migration-readiness claim is being closed | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
