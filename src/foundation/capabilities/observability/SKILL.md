---
name: observability
description: "`analysis-agent`/`task-agent`/`review-agent`: primary-Skill-selected for logs, metrics, traces, alerts, SLI/SLO, or diagnostics; never task owner; skip without signal impact."
---

# observability

## Registry Trigger

**Use when**

- design logs metrics traces dashboards alerts SLI and diagnostic context

**Do not use when**

- no task-local observability decision is required

## Skill Role

Own privacy-safe decision-bearing signals and actions for the named risk.

## High-Value Rules

- Select signals from material impact.
- Bound sensitive fields, cardinality, and sampling.
- Propagate correlation only across evidence-bearing boundaries.
- Bind every alert to an owner and response.

## Anti-Patterns

- Local success substituted for end-to-end signal and action evidence.

## Stop Conditions

Stop when a critical path has no bounded signal or owned response.

## Output Contract

- observability plan with signals dashboards alerts and investigation paths, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | signal alert SLI trace or runbook choices remain unresolved | operator decision and existing objective determine required signals | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects user impact correlation metrics traces alerts or ownership | no operational signal or response behavior changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | dashboard alert propagation or runbook claims need fresh proof | current queries configs and synthetic checks prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
