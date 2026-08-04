---
name: agent-execution-discipline
description: "Use when execution-evidence source, freshness, scope, reproducibility, reuse, or contradictions are uncertain; skip when current claim-matched evidence is established."
---

# Agent Execution Discipline

## Registry Trigger

**Use when**

- a material execution claim depends on evidence with uncertain source, freshness, scope, or reproducibility
- evidence reuse or a contradiction needs a task-local validity decision

**Do not use when**

- current claim-matched evidence is already established and no contradiction exists
- the task asks to create, run, or repair validation rather than assess supplied evidence

## Skill Role

Assess evidence for one scoped execution claim. Decide which artifacts are invalid, reusable, contradictory, or insufficient without defining completion or execution workflow.

## Inputs

- the exact claim, scope, and artifact identity
- evidence artifacts with source, inputs, producer, and time
- reproduction, reuse, and contradiction facts

## High-Value Rules

- For the scoped claim, assess artifact bindings against the exact claim, source or producer, input identity, time, and scope.
- Mark evidence invalid when provenance is absent, content is truncated or unsafe, or scope or identity does not match.
- Verify freshness from artifact identity and changes capable of invalidating it.
- Verify reproducibility from the available procedure, inputs, environment, and observable result.
- Mark evidence reusable only for the same claim, scope, input identity, and mechanism; otherwise record the mismatch.
- When assessed artifacts conflict, preserve the separate claims and state their unresolved relationship.
- State the proof limit and residual uncertainty of every decision.

## Anti-Patterns

- An exit status or summary without its artifact and source does not establish scope.
- A new timestamp does not prove freshness when identity or inputs differ.
- Repeated summaries do not establish independent reproducibility.
- Absence of a visible contradiction is not confirmation.

## Execution Checklist

1. Name the claim and its exact scope.
2. For the scoped claim, identify artifact source, producer, inputs, identity, and time.
3. Decide freshness and reproducibility for the current claim.
4. For the scoped claim, classify its evidence artifacts as invalid, reusable, contradictory, or insufficient.
5. Record proof limits and residual uncertainty.

## Stop Conditions

- Return `insufficient` when source, identity, or scope cannot be established.
- Return `contradictory` when conflicts cannot be resolved from the supplied evidence, and name the missing fact.

## Output Contract

- execution-evidence assessment with claim, source, freshness, scope, reproducibility, reuse decision, invalid evidence, reusable evidence, contradictions, proof limit, and residual uncertainty

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | source freshness scope or reproducibility must be assessed consistently | the evidence already has a current claim matched assessment | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence reuse](references/evidence-reuse-patterns.md) | evidence-pattern | reuse invalidation or contradictory artifacts need classification | no artifact reuse invalidation or contradiction decision is required | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
