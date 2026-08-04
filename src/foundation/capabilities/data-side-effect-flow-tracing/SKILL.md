---
name: data-side-effect-flow-tracing
description: "`analysis-agent`/`task-agent`/`review-agent`: use when persistence, cache, events, external I/O, or compensation may hide or misorder side effects; skip unchanged flows."
---

# data-side-effect-flow-tracing

## Registry Trigger

**Use when**

- data side effect flow, input validation, mapping, policy, mutation, transaction, persistence, cache, event, external IO, logging, metrics, file IO, clock, random, env, outbox, publish after commit, idempotency, compensation, hidden side effect, mapper, getter

**Do not use when**

- no task-local data side effect flow tracing decision is required

## Skill Role

Trace data authority and side effects through validation, mapping, decisions, state mutation, persistence, cache, events, external I/O, observation, failure, and recovery. Exclude detailed mechanism design.

## High-Value Rules

- **Start from authoritative input and intended effect.** Name source, identity, tenant or subject binding, canonical value, business decision, expected durable state, and externally observable outcomes.
- **Trace every reachable mutation boundary.** Follow direct and indirect writes through mappers, callbacks, lifecycle hooks, repositories, generated code, cache, events, files, network calls, logs, metrics, and cleanup.
- **Record order and consistency.** Identify transaction boundaries, commit points, publication, acknowledgement, cache invalidation, external effects, and which combinations can partially succeed.
- **Bind repeat behavior to logical identity.** Define duplicate requests, retries, replay, concurrent writers, late results, and whether each side effect is idempotent, deduplicated, compensated, reconciled, or prohibited.
- **Preserve unknown outcomes.** Treat timeout, cancellation, crash, and lost acknowledgement as unresolved when commit status is not proven, and locate the authority that can reconcile before repeat action.
- **Include negative and cleanup effects.** Trace denied and failed paths, resource release, rollback, compensating actions, tombstones, deletion, and observation so failure cannot leave hidden durable state.
- **Prove the flow with current evidence.** Combine source and configuration reachability, focused tests or fault injection, persisted-state checks, emitted effects, and unverified external paths with residual owners.

## Anti-Patterns

- Stop tracing at the service return while persistence hooks, events, cache, files, or external effects continue.
- Assume a transaction covers effects committed by another store, process, provider, or asynchronous consumer.
- Retry after timeout or partial failure without authoritative status and logical operation identity.

## Stop Conditions

Escalate when data or writer authority is unknown, a consequential side effect lacks ownership, partial success cannot reconcile, or repeat delivery can duplicate effects. Also escalate when deletion or compensation is irreversible, or external and generated paths cannot be inspected.

## Output Contract

- side-effect flow with authoritative inputs, mutations and effects, order and commit boundaries, repeat and unknown outcomes, failure and cleanup paths, evidence limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Ordering, compensation, nondeterminism, or publication mechanisms need selection | The affected path is pure and side-effect free | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Flow crosses persistence, cache, events, external IO, or retries | No mutation or external interaction is reachable | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Flow safety depends on fresh call-order and failure-path evidence | No effect-ordering or purity claim awaits proof | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
