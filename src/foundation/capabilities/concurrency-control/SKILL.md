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

- Name the resource and invariant, then choose the narrowest conditional update, compare-and-swap, transaction, partition, or scoped lock.
- Choose optimistic or pessimistic control from measured contention, storage semantics, latency, and recovery cost; no universal conflict-rate threshold is valid.
- Define retry, reject, merge, or escalation; when duplicate effects and the response contract require it, reuse a durable outcome, otherwise prove natural idempotence or safe re-execution.
- Bound and release locks and leases, order multi-resource locks, and reject stale distributed-lease holders with monotonic fencing.
- Prove the invariant with synchronized overlap and allowed-outcome assertions; add race or stress tooling when risk warrants it.

## Anti-Patterns

- A `read → decide → act` sequence is unsafe unless the store enforces the decision atomically.
- Enqueue deduplication does not make consumer side effects exactly once.

## Execution Checklist

1. Identify resources, invariants, overlap, and atomicity gaps.
2. Specify mechanism, conflict response, retry/idempotency, lock order, and fencing.
3. Verify deterministic race outcomes and the forbidden stale or duplicate effect.

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
