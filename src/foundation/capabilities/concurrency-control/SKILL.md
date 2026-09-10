---
name: concurrency-control
description: "`analysis-agent`/`task-agent`/`review-agent`: primary-Skill-selected for races, locks, optimistic conflicts, or worker overlap; never task owner; skip without concurrency impact."
---

# concurrency-control

## Registry Trigger

**Use when**

- control concurrent writes races locks leases optimistic conflicts and queues

**Do not use when**

- no task-local concurrency control decision is required

## Skill Role

Preserve named invariants under overlapping writes, retries, leases, redelivery, and stale ownership.

## High-Value Rules

- Select the narrowest current-store control that preserves the named invariant under reachable overlap.
- Define conflict outcomes, retry and idempotence, lock or lease lifecycle, order, and fencing for affected actors.
- Prove allowed and forbidden concurrent outcomes.

## Anti-Patterns

- Local success substituted for evidence of the concurrency control contract.

## Stop Conditions

Escalate when money, inventory, permissions, quotas, or cross-service reservations can violate an invariant, a distributed lease lacks fencing, or recovery is unproven.

## Output Contract

- concurrency plan with critical sections locks conflicts and tests, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Lost updates, stale ownership, deadlocks, or contention need mechanism selection | No overlapping actor can mutate the affected invariant | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Concurrency spans retries, cancellation or timeout, lease ownership or another time-derived ownership claim, lock order, version reuse or ABA, duplicate effects, or scheduling fairness | The resource has one serialized owner | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Safety claims require synchronized overlap or contention artifacts | No interleaving or ownership claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
