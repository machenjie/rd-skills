---
name: contract-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use for provider-consumer compatibility of APIs, events, schemas, or behavior; skip without independent consumer/version risk."
---

# contract-testing

## Registry Trigger

**Use when**

- prove provider-consumer compatibility for an API, event, schema, generated client, or captured external behavior

**Do not use when**

- the change has no independent consumer expectation, compatibility transition, or retained-message/replay risk

## Skill Role

Prove executable compatibility on named provider-consumer surfaces. Exclude broad consumer discovery, contract design, and release verdicts.

## High-Value Rules

- Name provider, consumers, contract source, coexisting versions, and compatibility direction; provider self-test is insufficient.
- Pair provider proof with named consumer/generated-client semantic proof; retain unrepresented consumers.
- Load only the named Reference for active strategy, closure, or evidence.

## Anti-Patterns

- Local success substituted for evidence of the contract testing contract.

## Stop Conditions

- Stop when unknown/deployed consumers, retained messages, undocumented behavior, or unavailable environments prevent an owned bounded claim.

## Output Contract

- provider-consumer compatibility decision with covered versions, semantic expectations, executable proof, freshness, and explicit non-proof boundaries

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Compatibility direction protocol mixed versions retained payloads generated clients or external behavior leave proof choices open | One named provider consumer surface and its compatibility rule resolve the decision | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Several semantic version consumer fixture replay or rollout decisions must close together | No provider consumer expectation or compatibility behavior changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Provider consumer mixed-version fixture broker registry or generated-client claims need fresh scoped proof | Fresh named-provider and named-consumer results close the bounded compatibility claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
