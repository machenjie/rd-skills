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

- Define durable business, workflow, run, step, command, effect, attempt, tenant, and definition-version identity with persisted state before dispatch.
- Record transition authority, guards, fences, timestamps, terminal meaning, and invalid legacy state.
- Correlate commands and results to workflow, step, and effect while rejecting send or broker acknowledgement as completion.
- Preserve unknown outcomes after timeout, crash, cancellation, or lost response until participant authority or reconciliation proves the effect.
- Require forward and compensating effects to be idempotent or durably deduplicated, with compensation inputs, preconditions, pivots, ordering, and convergence recorded.
- Reconcile desired state against participant facts with bounded, attributable corrections safe under concurrent progress.
- Detect stuck or poison work and constrain repair by target, authority, precondition, dry run, evidence, audit identity, and terminal outcome.
- Define active-workflow version compatibility, replay, migration or pinning, and retirement evidence.

## Anti-Patterns

- Duplicate delivery commits an effect twice.
- Lost completion leaves a committed effect unfinished.
- Wrong compensation violates current business state.
- Partial ordering advances a dependency early.
- Poison or stuck work loops or blocks progress.
- Old-version execution misreads state or commands.
- Manual repair changes state without audit evidence.

## Execution Checklist

- Fault before/after dispatch and effect, before result persistence, and during compensation.
- Exercise duplicate, reordered, delayed, poison, lost-response, stuck, repair, and participant-drift cases.
- Replay representative old/new definitions against histories and mixed participant versions.

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
