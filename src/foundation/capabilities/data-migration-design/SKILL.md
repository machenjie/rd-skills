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

Own data-state transitions and cutover safety; exclude business rules and production operation.

## High-Value Rules

- Bind source and target authority plus mixed-version readers and writers to one cutover state.
- Coordinate live writes and backfill through owned ordering, resumability, semantic validation, and recovery.
- Block destructive cleanup until readers retire and reconciliation, recovery, and ownership are proven.

## Anti-Patterns

- Do not treat moved rows or local success as semantic correctness, or race live writers with an unowned backfill.

## Stop Conditions

- Stop on unknown authority or writers, unsafe mixed versions or ordering, non-resumable execution, unproved validation or recovery, or unowned sensitive data.

## Output Contract

- migration decision with source and target state, compatibility sequence, writer and backfill coordination, resumability, validation evidence, rollback limits, completion condition, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Migration phases, backfill, cutover, or rollback tiers remain open | No schema, data, or mixed-version transition changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Migration spans locks, checkpoints, dual operation, or irreversible cleanup | An additive metadata change needs no data movement | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Safety claims require fresh dry runs, counts, or restore rehearsal | No migration-readiness claim is being closed | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
