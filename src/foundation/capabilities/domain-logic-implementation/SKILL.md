---
name: domain-logic-implementation
description: "`analysis-agent`/`task-agent`: use when an invariant, transition, calculation, or policy needs one domain authority; skip orchestration, storage, mapping, and unchanged-rule work."
---

# domain-logic-implementation

## Registry Trigger

**Use when**

- implement domain invariant transition calculation policy rule authority failure semantics and bypass protection

**Do not use when**

- work changes orchestration persistence transport or model translation without changing domain behavior

## Skill Role

Implement the authority that accepts or rejects reachable state transitions, calculations, or policy results. Select aggregates, value objects, policies, or domain services only when their authority fits.

## High-Value Rules

- Select the authority that has the facts and lifecycle needed to reject an invalid decision for reachable callers. Object type, framework convention, or method size does not determine ownership.
- Scan API, admin, import, job, consumer, migration, fixture, ORM, and direct-write paths that can create or mutate the affected state. Record uninspected writers instead of assuming the named method is exclusive.
- Reject invalid state before durable or external effects through selected constraints, locks, versions, or idempotency that reinforce readable domain behavior.
- Define transitions and calculations with trusted inputs, allowed and denied outcomes, basis/version, units, precision, rounding, currency/timezone/effective-time semantics, and terminal behavior that the task actually changes.
- Return domain decisions, typed denials, or domain events without performing persistence, provider calls, queueing, file I/O, cache mutation, or transport mapping inside the rule authority.
- When a rule spans consistency boundaries, name the application, transaction, idempotency, compensation, or reconciliation owner. Do not claim a single aggregate guarantee that no local authority can enforce.
- Account for existing persisted values, old and new rule versions, replay, backfill, projections, and external consumers when rule evolution can reinterpret historical state.

## Anti-Patterns

- Using controller, UI, service prechecks, fixtures, or ORM hooks as the final protection for a business invariant.
- Creating a domain service, value object, or aggregate because a pattern catalog suggests it rather than because authority and lifecycle evidence require it.
- Copying formulas, transition guards, or policy branches into reporting, mappers, jobs, and consumers.
- Treating happy-path tests or a database constraint as proof that bypasses, denials, historical data, and concurrent writes are safe.

## Stop Conditions

- Escalate when rule truth or authority is disputed, or a cross-boundary invariant has no consistency owner. Also escalate when historical data violates the new rule, or money, permission, entitlement, inventory, compliance, or irreversible state lacks denied and recovery semantics.

## Output Contract

- Return a domain-rule contract: state authority, invariants, transitions, calculations, typed outcomes, bypasses, evolution defenses, evidence limits, and consistency owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Rule authority lifecycle calculation cross-boundary consistency or evolution leaves competing placements | Current facts and reachable writers select one bounded authority | task-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A rule change crosses writers denials calculations concurrency defenses historical data or consumers | No invariant transition calculation policy or existing-state interpretation changes | task-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Authority bypass denial calculation evolution or race claims need current source and tests | Fresh scoped rule and writer evidence closes the accepted claim | task-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
