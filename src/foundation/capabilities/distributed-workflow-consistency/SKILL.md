---
name: distributed-workflow-consistency
description: "Use for distributed workflow consistency, unknown effects, compensation, reconciliation, repair, or evolution. Skip atomic transactions, local retry, schema-only, and engine work."
---

# distributed-workflow-consistency

## Registry Trigger

**Use when**

- An operation spans independently committed service effects.
- Partial progress needs durable recovery or repair.

**Do not use when**

- Route one-store atomicity to `transaction-consistency`, local repetition to `idempotency-retry-design`, and schema-only work to its messaging or API owner.
- Do not design a workflow engine, SDK, scheduler, or administration product.

## Skill Role

Define cross-service recovery contracts without replacing participant or transport owners.

## High-Value Rules

- Persist workflow, step, command, effect, attempt, tenant, version, and authoritative state before dispatch.
- Preserve command and effect correlation plus unknown outcomes until participant facts or reconciliation resolve them.
- Define idempotent forward, compensation, reconciliation, repair, stuck handling, audit, versioning, replay, and terminal evidence.

## Anti-Patterns

- Local success substituted for evidence of the distributed workflow consistency contract.

## Stop Conditions

- Stop on ambiguous identity, missing durable state, unknown effect authority, unsafe compensation, or unowned stuck work.
- Stop repair without authorization, audit, convergence checks, and repeat safety.
- Route atomicity, retry, schema, provider guarantees, and engine implementation to their owners.

## Output Contract

- workflow-consistency decision with identity, state, correlation, unknown outcomes, recovery, repair, versioning, limits, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [identity state and unknown outcomes](references/identity-state-and-unknown-outcomes.md) | targeted | Workflow identity durable step state command/effect correlation or unknown outcomes remain unresolved | One local operation has no cross-service workflow state | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, proof-limit |
| [compensation convergence and reconciliation](references/compensation-convergence-and-reconciliation.md) | targeted | Partial success needs compensation forward recovery convergence or participant reconciliation | Atomic rollback or safe local retry already resolves the failure | analysis-agent, task-agent, review-agent | failure-decision, selected-approach, residual-risk |
| [stuck manual repair and versioning](references/stuck-manual-repair-and-versioning.md) | targeted | Stuck poison repair replay reset or active-workflow version evolution changes | No operational recovery or version-skew boundary changes | analysis-agent, task-agent, review-agent | failure-decision, validation-plan, proof-limit |
