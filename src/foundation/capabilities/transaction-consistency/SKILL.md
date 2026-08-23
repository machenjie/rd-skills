---
name: transaction-consistency
description: "Use with analysis-agent or task-agent for task-local transaction, isolation, and conflict decisions. Do not use without a transaction decision or as task owner."
---

# transaction-consistency

## Registry Trigger

**Use when**

- design transaction boundaries isolation consistency locking and conflict handling

**Do not use when**

- no task-local transaction consistency decision is required

## Skill Role

Protect named invariants through explicit transaction boundaries, isolation assumptions, effect ordering, conflict handling, and recovery proof.

## High-Value Rules

- Start from the named invariant and target anomaly. Confirm the actual database, storage engine, ORM behavior, connection settings, default isolation, and retry semantics before selecting isolation or locking.
- Bound atomic work to writes and reads that must succeed together. A transaction, conditional write, optimistic check, outbox, saga, or compensation is a candidate only when actual atomic boundaries and partial-failure consequences justify it.
- Keep remote or slow I/O outside held locks when latency and contention evidence make it unsafe; define intent, commit, side-effect ordering, conflict handling, and recovery explicitly.

## Anti-Patterns

- Local success substituted for evidence of the transaction consistency contract.

## Stop Conditions

- Escalate money, inventory, quota, ownership, cross-service atomicity, multi-row lock ordering, or failed-compensation risk when the invariant, recovery owner, or current datastore evidence remains unclear.

## Output Contract

- consistency plan with transaction scope isolation conflicts and tests

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | invariant anomaly or effect ordering leaves consistency mechanisms unresolved | actual atomic boundary selects one proven consistency mechanism | analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects atomic writes isolation conflicts remote effects or recovery | no transaction invariant or partial-failure behavior changes | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | isolation ordering idempotency or reconciliation claims need fresh proof | current handlers datastore tests and artifacts prove each claim | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
