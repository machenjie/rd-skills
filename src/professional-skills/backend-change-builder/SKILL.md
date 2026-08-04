---
name: backend-change-builder
description: "Use `task-agent` for bounded backend service, API, worker, or repair changes, loading authorization, consistency, retry, contract, and rollout guidance only when triggered. Skip frontend-only and read-only work."
---

# backend-change-builder

## Role

Support `task-agent` in preserving invariants across bounded backend changes.

## When To Use

- backend behavior change
- service or worker change

## Do Not Use

- frontend only
- source inspection only

## Required Inputs

- domain invariants
- authorization and failure-contract evidence
- transaction, delivery, and recovery constraints

## Professional Decision Rules

- When the change affects untrusted input, identity, resource scope, or tenant scope, preserve validation and server-side authorization before disclosure or mutation.
- When multi-step writes or side effects can partially succeed, define the atomicity, ordering, recovery, and observable failure outcome needed to preserve the affected invariant.
- When execution or delivery can repeat, define duplicate behavior and idempotency; add acknowledgement, replay, or poison-message recovery only for message or job delivery paths.
- Preserve compatible error contracts when failure behavior changes.
- Select redacted observability from current API and platform policy.

## High-Value Gotchas

- Authorization after loading an object can leak existence or data.
- Publishing side effects before commit creates phantom events.
- Retries without idempotency duplicate money, jobs, or notifications.

## Execution Checklist

1. Trace each affected invariant through authorization, mutation, side effects, and failure outcomes.
2. Choose transaction, idempotency, and recovery controls from the reachable failure paths.
3. Implement the bounded change while preserving compatible errors and redacted diagnostics.
4. Stop closure when a triggered invariant lacks negative-path or recovery evidence.

## Stop / Escalation Conditions

- Stop when behavior, ownership, validation, or a triggered invariant remains implicit.
- Stop repair work without an accepted finding or verified failure mechanism.
- Stop new structure until placement, ownership, dependency direction, and the simpler local option are evaluated.
- Stop sensitive or external actions without authority, redaction, recovery, and fresh evidence.

## Output Contract

- changed backend invariants and boundaries
- authorization, consistency, delivery, and recovery decisions
- negative-path and recovery proof limits
- residual operational risk

For targeted implementation fields and gates, load `references/backend-output-and-gates.md`.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [backend output and gates](references/backend-output-and-gates.md) | targeted | extended fields apply when implementation closure depends on edit-to-validation ordering or repair proof | The root contract is sufficient for bounded implementation | task-agent | gate-decision, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | A bounded implementation needs quick checks for its triggered backend risks | The root contract is enough or extended proof fields are needed | task-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing backend change builder references require dependency, conflict, or output-fragment selection | the backend change builder root or a task-named reference already resolves selection | task-agent | reference-selection |
| [proactive triggers](references/proactive-triggers.md) | targeted | Authorization, tenancy, retries, async, public contracts, transactions, irreversible mutation, or AI-generated backend code are material | No hidden backend escalator is present | task-agent | boundary-decision, residual-risk |
| [professional modes](references/professional-modes.md) | mode-contract | L3+ implementation or accepted-finding repair needs mode-specific proof and ownership limits | The root contract determines implementation evidence or the task is still diagnosis/independent review | task-agent | mode-result, proof-limit |
| [solution optimality](references/solution-optimality.md) | targeted | An accepted implementation chooses a material algorithm, query pattern, cache, batch/stream boundary, concurrency control, pool, queue, or other resource-sensitive design | No runtime/resource tradeoff is material or current system evidence already fixes the mechanism | task-agent | selected-approach, residual-risk |
