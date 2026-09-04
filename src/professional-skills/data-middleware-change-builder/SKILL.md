---
name: data-middleware-change-builder
description: "Use `analysis-agent` or `task-agent` for database, cache, queue, search, consistency, or source-of-truth work; skip unrelated work."
---

# data-middleware-change-builder

## Role

- **Analysis mode (`analysis-agent`):** Map ownership, failure, recovery, and proof.
- **Task mode (`task-agent`):** Apply the accepted state change.

## When To Use

- database cache queue or search change
- consistency risk

## Do Not Use

- no middleware impact
- unrelated source inspection

## Required Inputs

- source of truth evidence and failure requirements
- **Analysis mode (`analysis-agent`):** access patterns, consistency model, and current read, write, and recovery evidence.
- **Task mode (`task-agent`):** accepted state transition, migration, replay, and rollback checks.

## Professional Decision Rules

- Keep state, consistency, transaction, delivery, migration, and recovery with their owner.
- Require resumable progress and invariant validation before cleanup.
- Load one Reference for its open output.

## High-Value Gotchas

- A derived store can look healthy while diverging from its source of truth.
- Retry can duplicate an effect when durable identity or acknowledgement ordering is unclear.
- Successful movement or local commit does not prove invariant preservation, recovery, or downstream compatibility.

## Execution Checklist

- **Analysis mode:** Map source and derived ownership, readers and writers, invariants, consistency, migration, recovery, and current evidence limits before selecting the boundary.
- **Task mode:** Apply the accepted state transition with bounded execution, replay or idempotency, reconciliation, rollback or forward repair, redaction, and post-edit validation.
- Verify failure behavior at the real store, cache, queue, search, or migration boundary.
- Record skipped paths and current proof limits.
- Stop when ownership, authority, irreversible effects, cleanup, or recovery evidence remains unresolved.

## Stop / Escalation Conditions

- Stop on unowned state/recovery or unsafe tool execution.

## Output Contract

- **Analysis mode (`analysis-agent`):** state-ownership decision and consistency, migration, and recovery model.
- **Task mode (`task-agent`):** stateful boundary changes, replay and reconciliation evidence, and unresolved recovery risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 review needs checks for source of truth, consistency, access patterns, indexes, cache, queues, search, storage, migrations, lifecycle, observability, and evidence | The inline quality gate is enough or detailed evidence/recovery patterns are required | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on query-plan artifacts, cache tests, queue/replay proof, migration/backfill reports, search cutover evidence, freshness, or proof limits | No data correctness claim depends on runtime evidence or the body evidence contract is sufficient | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing data middleware change builder references require dependency, conflict, or output-fragment selection | the data middleware change builder root or a task-named reference already resolves selection | analysis-agent, task-agent | reference-selection |
| [recovery](references/recovery-patterns.md) | benchmark-pattern | Failure recovery, replay, rollback, reconciliation, release watch, or owner/trigger/stop condition is material to correctness | The change has no material recovery path beyond normal tests and the body quality gate is enough | analysis-agent, task-agent | option-comparison, selected-approach |
