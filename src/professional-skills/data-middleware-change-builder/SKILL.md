---
name: data-middleware-change-builder
description: "Use `analysis-agent` for database, cache, queue, search, or consistency risk, or `task-agent` for bounded middleware changes. Skip work without middleware or source-of-truth impact and unrelated inspection."
---

# data-middleware-change-builder

## Role

Support `analysis-agent` and `task-agent` for bounded persistence, cache, queue, search, streaming, and middleware changes.

- **Analysis mode (`analysis-agent`):** Classify state ownership, consistency, migration, and recovery requirements.
- **Task mode (`task-agent`):** Apply the accepted stateful boundary and recovery behavior.

## When To Use

- database cache queue or search change
- consistency risk

## Do Not Use

- no middleware impact
- unrelated source inspection

## Required Inputs

- source of truth evidence
- failure requirements
- **Analysis mode (`analysis-agent`):** access patterns, consistency model, and current read, write, and recovery evidence.
- **Task mode (`task-agent`):** accepted state transition with migration, replay, and rollback checks.

## Professional Decision Rules

- Name the source of truth, consistency model, transaction boundary, and ownership for every stateful change.
- Design migrations for version coexistence, backfill idempotency, restartability, verification, and rollback.
- For caches and queues, define invalidation, ordering, duplication, replay, poison-message, and degradation behavior.
- Use realistic data volume and concurrency evidence for query, index, lock, and partition choices.

## High-Value Gotchas

- Cache invalidation without a source-of-truth rule serves stale data.
- A migration that cannot resume safely turns failure into manual recovery.
- Queue acknowledgement order can lose or duplicate work.

## Execution Checklist

1. Trace source-of-truth ownership through reads, writes, invalidation, delivery, and recovery.
2. Choose consistency, migration, replay, and rollback mechanisms from actual sink semantics.
3. Verify query plans, cardinality, idempotency, and failure restartability where triggered.
4. **Analysis mode:** select consistency and recovery behavior from sink evidence.
5. **Task mode:** apply the accepted boundary with replay and reconciliation behavior.
6. Stop when state ownership or reconciliation behavior remains implicit.

## Stop / Escalation Conditions

- Stop implementation when source of truth, consistency model, access pattern, cache invalidation, queue delivery semantics, or migration rollback is implicit.
- Stop query/index approval when `EXPLAIN`/plan evidence, realistic cardinality, named query, or write-overhead judgment is missing.
- Stop queue/cache/search/migration approval when idempotency, DLQ/replay, stampede/fallback, shadow-index/cutover, batching, rollback, or reconciliation proof is missing.
- Stop tool execution when database, cache, queue, search, migration, backfill, replay, repair, or connector action lacks permission/sandbox, dry-run/read-only scope, rollback/revert path, and redaction evidence.

## Output Contract

- **Analysis mode (`analysis-agent`):** state-ownership decision; consistency, migration, and recovery model.
- **Task mode (`task-agent`):** stateful boundary changes; replay and reconciliation evidence; unresolved recovery risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 review needs checks for source of truth, consistency, access patterns, indexes, cache, queues, search, storage, migrations, lifecycle, observability, and evidence | The inline quality gate is enough or detailed evidence/recovery patterns are required | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on query-plan artifacts, cache tests, queue/replay proof, migration/backfill reports, search cutover evidence, freshness, or proof limits | No data correctness claim depends on runtime evidence or the body evidence contract is sufficient | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing data middleware change builder references require dependency, conflict, or output-fragment selection | the data middleware change builder root or a task-named reference already resolves selection | analysis-agent, task-agent | reference-selection |
| [recovery](references/recovery-patterns.md) | benchmark-pattern | Failure recovery, replay, rollback, reconciliation, release watch, or owner/trigger/stop condition is material to correctness | The change has no material recovery path beyond normal tests and the body quality gate is enough | analysis-agent, task-agent | option-comparison, selected-approach |
